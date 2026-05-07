from dataclasses import replace

from ai.llm_provider import LLMResult, build_llm_provider
from config import load_settings
from response_generator import ResponseGenerator


class FakeLLMProvider:
    provider_name = "fake"

    def generate(self, prompt: str, current_user: str | None = None) -> LLMResult:
        return LLMResult(
            text=f"LLM answer for {current_user}: {prompt}",
            provider=self.provider_name,
            ok=True,
        )


def test_llm_disabled_by_default():
    settings = replace(load_settings(), llm_provider="none")

    provider = build_llm_provider(settings)
    result = provider.generate("what is ai")

    assert result.ok is False
    assert provider.provider_name == "none"


def test_gemini_provider_can_be_selected_without_importing_sdk():
    settings = replace(load_settings(), llm_provider="gemini")

    provider = build_llm_provider(settings)

    assert provider.provider_name == "gemini"


def test_response_generator_uses_llm_for_fallback():
    generator = ResponseGenerator(llm_provider=FakeLLMProvider())

    response = generator.generate("explain embedded ai", current_user="Boudy")

    assert response.intent.name == "fallback"
    assert response.text == "LLM answer for Boudy: explain embedded ai"


def test_response_generator_keeps_simple_intents_local():
    generator = ResponseGenerator(llm_provider=FakeLLMProvider())

    response = generator.generate("hello", current_user="Boudy")

    assert response.intent.name == "greeting"
    assert "Hello Boudy" in response.text
