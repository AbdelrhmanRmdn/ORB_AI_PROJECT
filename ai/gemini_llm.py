from __future__ import annotations

import re
import time

from config import Settings, SETTINGS
from ai.llm_provider import LLMResult
from ai.prompts import ORB_SYSTEM_PROMPT, build_user_prompt
from logging_config import get_logger


logger = get_logger("ai.gemini")


class GeminiLLMProvider:
    provider_name = "gemini"

    def __init__(self, settings: Settings = SETTINGS) -> None:
        self.settings = settings
        self._client = None
        self._rate_limited_until = 0.0

    def generate(self, prompt: str, current_user: str | None = None) -> LLMResult:
        wait_seconds = int(self._rate_limited_until - time.time())
        if wait_seconds > 0:
            return LLMResult(
                text=f"Gemini is rate-limited. Please wait about {wait_seconds} seconds and try again.",
                provider=self.provider_name,
                ok=False,
                error="rate_limited",
            )

        try:
            client = self._get_client()
            full_prompt = (
                f"{ORB_SYSTEM_PROMPT}\n\n"
                f"{build_user_prompt(prompt, current_user=current_user)}"
            )
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=full_prompt,
            )
            text = getattr(response, "text", "").strip()
            if not text:
                return LLMResult(
                    text="I could not generate a useful answer.",
                    provider=self.provider_name,
                    ok=False,
                    error="empty_response",
                )
            return LLMResult(text=text, provider=self.provider_name, ok=True)
        except Exception as exc:
            error = str(exc)
            self._update_rate_limit_cooldown(error)
            logger.warning("Gemini LLM request failed: %s", error)
            return LLMResult(
                text="I could not reach the Gemini AI model right now.",
                provider=self.provider_name,
                ok=False,
                error=error,
            )

    def _get_client(self):
        if self._client is not None:
            return self._client

        from google import genai

        api_key = self.settings.gemini_api_key.strip()
        self._client = genai.Client(api_key=api_key) if api_key else genai.Client()
        return self._client

    def _update_rate_limit_cooldown(self, error: str) -> None:
        if "429" not in error and "RESOURCE_EXHAUSTED" not in error:
            return

        match = re.search(
            r"(?:retryDelay['\"]?: ['\"]|retry in )(\d+(?:\.\d+)?)s",
            error,
            flags=re.IGNORECASE,
        )
        wait_seconds = float(match.group(1)) if match else 60.0
        self._rate_limited_until = max(
            self._rate_limited_until,
            time.time() + wait_seconds,
        )
