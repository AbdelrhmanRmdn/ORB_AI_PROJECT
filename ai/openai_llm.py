from __future__ import annotations

from config import Settings, SETTINGS
from ai.llm_provider import LLMResult
from ai.prompts import ORB_SYSTEM_PROMPT, build_user_prompt
from logging_config import get_logger


logger = get_logger("ai.openai")


class OpenAILLMProvider:
    provider_name = "openai"

    def __init__(self, settings: Settings = SETTINGS) -> None:
        self.settings = settings
        self._client = None

    def generate(self, prompt: str, current_user: str | None = None) -> LLMResult:
        try:
            client = self._get_client()
            response = client.responses.create(
                model=self.settings.openai_model,
                instructions=ORB_SYSTEM_PROMPT,
                input=build_user_prompt(prompt, current_user=current_user),
                max_output_tokens=self.settings.llm_max_tokens,
                temperature=self.settings.llm_temperature,
            )
            text = getattr(response, "output_text", "").strip()
            if not text:
                return LLMResult(
                    text="I could not generate a useful answer.",
                    provider=self.provider_name,
                    ok=False,
                    error="empty_response",
                )
            return LLMResult(text=text, provider=self.provider_name, ok=True)
        except Exception as exc:
            logger.warning("OpenAI LLM request failed: %s", exc)
            return LLMResult(
                text="I could not reach the online AI model right now.",
                provider=self.provider_name,
                ok=False,
                error=str(exc),
            )

    def _get_client(self):
        if self._client is not None:
            return self._client

        from openai import OpenAI

        self._client = OpenAI()
        return self._client
