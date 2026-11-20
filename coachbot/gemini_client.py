"""Gemini integration: structured JSON generation with retries, error handling and logs.

Uses Google's official `google-genai` SDK (the successor of the deprecated
`google-generativeai` package named in the brief).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from pydantic import ValidationError

from coachbot import config, demo, safety
from coachbot.features import Feature
from coachbot.logger import log_event, prompt_hash
from coachbot.prompts import build_prompt, system_instruction
from coachbot.schema import CoachPlan, parse_plan


@dataclass
class Params:
    temperature: float = config.DEFAULT_TEMPERATURE
    top_p: float = config.DEFAULT_TOP_P
    top_k: int = config.DEFAULT_TOP_K
    max_tokens: int = config.DEFAULT_MAX_TOKENS

    @classmethod
    def for_feature(cls, feature: Feature, max_tokens: int = config.DEFAULT_MAX_TOKENS) -> Params:
        return cls(feature.temperature, feature.top_p, feature.top_k, max_tokens)


@dataclass
class Result:
    status: str  # ok | demo | blocked | error
    plan: CoachPlan | None = None
    message: str = ""
    raw: str = ""
    prompt: str = ""
    system: str = ""
    model: str = ""
    params: Params = field(default_factory=Params)
    latency_s: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    attempts: int = 0
    flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _friendly_error(exc: Exception) -> tuple[str, bool]:
    """Map SDK errors to a user message and whether a retry could help."""
    code = getattr(exc, "code", None)
    if code in (400,) and "API key" in str(exc):
        return "Your Gemini API key was rejected. Check it in Streamlit secrets.", False
    if code in (401, 403):
        return "Your Gemini API key doesn't have access. Check the key and project.", False
    if code == 404:
        return "That model id isn't available for your key. Pick another model or use 'List my models'.", False
    if code == 429:
        return "Gemini rate limit reached — wait a minute and try again.", True
    if code in (500, 502, 503, 504):
        return "Gemini is busy right now. Retrying…", True
    if isinstance(exc, (ValidationError, ValueError)):
        return "Gemini returned malformed JSON.", True
    return f"Unexpected error: {type(exc).__name__}", True


class CoachEngine:
    """Generates plans with Gemini when an API key is set, otherwise with the demo engine."""

    def __init__(self, api_key: str | None, model: str = config.DEFAULT_MODEL):
        self.api_key = api_key or None
        self.model = model
        self._client = None
        if self.api_key:
            from google import genai  # imported lazily so demo mode needs no SDK

            self._client = genai.Client(api_key=self.api_key)

    @property
    def live(self) -> bool:
        return self._client is not None

    def list_models(self) -> list[str]:
        if not self._client:
            return []
        names = []
        for m in self._client.models.list():
            actions = getattr(m, "supported_actions", None) or []
            if not actions or "generateContent" in actions:
                names.append(m.name.removeprefix("models/"))
        return sorted(n for n in names if "gemini" in n)

    def generate(self, feature: Feature, profile: dict, extras: dict, params: Params) -> Result:
        free_text = " ".join(str(v) for v in extras.values()) + " " + profile.get("notes", "")
        screen = safety.screen_input(profile, free_text)
        system = system_instruction(profile)
        prompt = build_prompt(feature, profile, extras, screen.constraints)
        base = dict(prompt=prompt, system=system, model=self.model if self.live else "demo-engine",
                    params=params, warnings=screen.warnings)

        if not screen.allowed:
            result = Result(status="blocked", message=screen.reason, flags=[screen.kind], **base)
            self._log(feature, result)
            return result

        if not self.live:
            start = time.perf_counter()
            plan = demo.generate(feature, profile, extras, params.temperature)
            result = Result(status="demo", plan=plan, raw=plan.model_dump_json(indent=2),
                            latency_s=time.perf_counter() - start, attempts=1, **base)
            result.flags = safety.screen_output(result.raw)
            self._log(feature, result)
            return result

        return self._generate_live(feature, prompt, system, params, base)

    def _generate_live(self, feature: Feature, prompt: str, system: str, params: Params, base: dict) -> Result:
        from google.genai import types

        cfg = types.GenerateContentConfig(
            system_instruction=system,
            temperature=params.temperature,
            top_p=params.top_p,
            top_k=params.top_k,
            max_output_tokens=params.max_tokens,
            response_mime_type="application/json",
            response_schema=CoachPlan,
        )
        start = time.perf_counter()
        message, raw = "", ""
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                response = self._client.models.generate_content(model=self.model, contents=prompt, config=cfg)
                raw = response.text or ""
                plan = parse_plan(raw)
                usage = getattr(response, "usage_metadata", None)
                result = Result(
                    status="ok", plan=plan, raw=raw, latency_s=time.perf_counter() - start, attempts=attempt,
                    tokens_in=getattr(usage, "prompt_token_count", 0) or 0,
                    tokens_out=getattr(usage, "candidates_token_count", 0) or 0, **base,
                )
                result.flags = safety.screen_output(raw)
                if result.flags:
                    plan.safety_notes.insert(0, "⚠️ CoachBot removed or flagged advice that isn't safe for young athletes: "
                                                + ", ".join(result.flags) + ". Ignore those parts.")
                self._log(feature, result)
                return result
            except Exception as exc:  # noqa: BLE001 — every failure is classified and logged
                message, retry = _friendly_error(exc)
                if not retry or attempt == config.MAX_RETRIES:
                    break
                time.sleep(config.RETRY_BASE_SECONDS * 2 ** (attempt - 1))
        result = Result(status="error", message=message, raw=raw, latency_s=time.perf_counter() - start,
                        attempts=attempt, **base)
        self._log(feature, result)
        return result

    @staticmethod
    def _log(feature: Feature, result: Result) -> None:
        plan = result.plan
        log_event({
            "feature": feature.id, "prompt_version": feature.version, "status": result.status,
            "model": result.model, "temperature": result.params.temperature, "top_p": result.params.top_p,
            "top_k": result.params.top_k, "max_tokens": result.params.max_tokens,
            "latency_s": round(result.latency_s, 3), "attempts": result.attempts,
            "tokens_in": result.tokens_in, "tokens_out": result.tokens_out,
            "prompt_hash": prompt_hash(result.prompt), "sections": len(plan.sections) if plan else 0,
            "schedule_days": len(plan.weekly_plan) if plan else 0, "output_chars": len(result.raw),
            "safety_flags": result.flags, "message": result.message,
        })
