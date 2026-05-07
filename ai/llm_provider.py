from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from config import Settings, SETTINGS
from logging_config import get_logger


logger = get_logger("ai.llm_provider")


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    ok: bool
    error: str | None = None


class LLMProvider(Protocol):
    provider_name: str

    def generate(self, prompt: str, current_user: str | None = None) -> LLMResult:
        ...


class DisabledLLMProvider:
    provider_name = "none"

    def generate(self, prompt: str, current_user: str | None = None) -> LLMResult:
        return LLMResult(
            text="I heard you, but I am not sure how to help with that yet.",
            provider=self.provider_name,
            ok=False,
            error="LLM provider disabled",
        )


def build_llm_provider(settings: Settings = SETTINGS) -> LLMProvider:
    provider = settings.llm_provider.strip().lower()

    if provider in {"", "none", "disabled", "off"}:
        return DisabledLLMProvider()

    if provider == "openai":
        from ai.openai_llm import OpenAILLMProvider

        return OpenAILLMProvider(settings)

    if provider == "gemini":
        from ai.gemini_llm import GeminiLLMProvider

        return GeminiLLMProvider(settings)

    if provider == "ollama":
        from ai.ollama_llm import OllamaLLMProvider

        return OllamaLLMProvider(settings)

    logger.warning("Unknown LLM provider '%s'; falling back to disabled", provider)
    return DisabledLLMProvider()
