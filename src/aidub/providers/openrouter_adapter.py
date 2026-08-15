"""OpenRouter LLM adapter — single API key, 100+ models.

OpenRouter proxies requests to Gemini, GPT-4o, Claude, DeepSeek, Mistral,
LLaMA, Qwen, etc.  The endpoint is OpenAI-compatible, so we use the
``openai`` SDK pointed at ``https://openrouter.ai/api/v1``.

https://openrouter.ai/docs
"""

from __future__ import annotations

import logging
import time
from typing import Any

from aidub.contracts.base import Identifier
from aidub.providers.router import (
    LlmAdapter,
    LlmProviderError,
    LlmProviderKind,
    LlmRequest,
    LlmResponse,
)

logger = logging.getLogger(__name__)

# ── Recommended models for dubbing tasks ──────────────────────────────────────
# Translation quality (highest → lowest cost):
#   google/gemini-2.0-flash-001          — best Bengali support, fast, cheap
#   deepseek/deepseek-r1                 — chain-of-thought, great for nuance
#   openai/gpt-4o-mini                   — reliable, cheap, good quality
#   meta-llama/llama-3.3-70b-instruct    — strong free tier
#   google/gemini-2.5-pro                — highest quality, slower + pricier
DEFAULT_MODEL = "google/gemini-2.0-flash-001"


class OpenRouterAdapter:
    """
    LLM adapter that routes requests through OpenRouter.

    OpenRouter bills per-token at model-specific rates.  Priority order in
    ``LlmProviderRouter`` should put this first — it covers every model the
    other adapters target, so a single key is all that's needed during
    development.

    Args:
        api_key:    OpenRouter API key (``sk-or-…``).
        model:      OpenRouter model slug (e.g. ``google/gemini-2.0-flash-001``).
        site_url:   Your app URL (used in ``HTTP-Referer`` header for analytics).
        app_name:   Your app name (used in ``X-Title`` header).
        timeout_s:  HTTP request timeout in seconds.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        *,
        site_url: str = "",
        app_name: str = "aidub",
        timeout_s: float = 120.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._site_url = site_url
        self._app_name = app_name
        self._timeout_s = timeout_s
        self._client: Any | None = None  # lazy-init

    # ── LlmAdapter protocol ───────────────────────────────────────────────────

    @property
    def provider_kind(self) -> LlmProviderKind:
        return LlmProviderKind.OPENROUTER

    def complete(self, request: LlmRequest) -> LlmResponse:
        """Send a chat-completion request through OpenRouter."""
        client = self._get_client()
        messages = _build_messages(request)

        extra: dict[str, Any] = {}
        if request.json_mode:
            extra["response_format"] = {"type": "json_object"}

        t0 = time.monotonic()
        try:
            resp = client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                timeout=self._timeout_s,
                **extra,
            )
        except Exception as exc:
            raise LlmProviderError(
                "openrouter", f"HTTP error: {exc}", retryable=_is_retryable(exc)
            ) from exc

        latency_ms = (time.monotonic() - t0) * 1_000
        choice = resp.choices[0]
        content = (choice.message.content or "").strip()

        if not content:
            raise LlmProviderError(
                "openrouter", "empty response content", retryable=True
            )

        logger.debug(
            "openrouter: model=%s tokens=%s/%s latency=%.0fms",
            self._model,
            resp.usage.prompt_tokens if resp.usage else "?",
            resp.usage.completion_tokens if resp.usage else "?",
            latency_ms,
        )

        return LlmResponse(
            request_id=request.request_id,
            provider_kind=LlmProviderKind.OPENROUTER,
            model_name=self._model,
            content=content,
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
            latency_ms=round(latency_ms, 1),
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI  # type: ignore[import-not-found]
            except ImportError as exc:
                raise LlmProviderError(
                    "openrouter",
                    "openai package not installed — run: pip install openai",
                    retryable=False,
                ) from exc

            headers: dict[str, str] = {}
            if self._site_url:
                headers["HTTP-Referer"] = self._site_url
            if self._app_name:
                headers["X-Title"] = self._app_name

            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self.BASE_URL,
                default_headers=headers,
            )
        return self._client

    # ── Convenience: list available models ───────────────────────────────────

    def list_models(self) -> list[str]:
        """Return all model slugs available on OpenRouter (for UI pickers)."""
        import urllib.request
        import json as _json

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read())
        return [m["id"] for m in data.get("data", [])]


# ── Module helpers ────────────────────────────────────────────────────────────

def _build_messages(request: LlmRequest) -> list[dict[str, str]]:
    msgs: list[dict[str, str]] = []
    if request.system_prompt:
        msgs.append({"role": "system", "content": request.system_prompt})
    msgs.append({"role": "user", "content": request.user_prompt})
    return msgs


def _is_retryable(exc: Exception) -> bool:
    """Classify OpenAI SDK / HTTP errors as retryable or not."""
    msg = str(exc).lower()
    retryable_keywords = ("rate limit", "timeout", "503", "502", "529", "overloaded")
    non_retryable_keywords = ("401", "403", "invalid api key", "billing")
    if any(k in msg for k in non_retryable_keywords):
        return False
    if any(k in msg for k in retryable_keywords):
        return True
    return True  # default: retry unknown errors


__all__ = ["OpenRouterAdapter", "DEFAULT_MODEL"]
