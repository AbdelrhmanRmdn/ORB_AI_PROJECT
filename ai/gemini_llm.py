from __future__ import annotations

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

    def generate(self, prompt: str, current_user: str | None = None) -> LLMResult:
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
            logger.warning("Gemini LLM request failed: %s", exc)
            return LLMResult(
                text="I could not reach the Gemini AI model right now.",
                provider=self.provider_name,
                ok=False,
                error=str(exc),
            )

    def _get_client(self):
        if self._client is not None:
            return self._client

        from google import genai

        self._client = genai.Client()
        return self._client
