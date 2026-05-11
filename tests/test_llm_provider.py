from dataclasses import replace

from ai.gemini_llm import GeminiLLMProvider
from ai.llm_provider import LLMResult, build_llm_provider
from config import load_settings
from response_generator import ResponseGenerator


class FakeLLMProvider:
    provider_name = "fake"

    def __init__(self, ok: bool = True):
        self.ok = ok
        self.calls = 0

    def generate(self, prompt: str, current_user: str | None = None) -> LLMResult:
        self.calls += 1
        return LLMResult(
            text=f"LLM answer for {current_user}: {prompt}",
            provider=self.provider_name,
            ok=self.ok,
            error=None if self.ok else "fake_error",
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


def test_preferred_llm_fallback_only_calls_llm_once_on_failure():
    llm = FakeLLMProvider(ok=False)
    generator = ResponseGenerator(llm_provider=llm, prefer_llm_for_all=True)

    response = generator.generate("explain embedded ai", current_user="Boudy")

    assert response.intent.name == "fallback"
    assert response.text == "LLM answer for Boudy: explain embedded ai"
    assert llm.calls == 1


def test_gemini_provider_uses_cooldown_after_rate_limit():
    provider = GeminiLLMProvider()
    provider._update_rate_limit_cooldown("429 RESOURCE_EXHAUSTED. Please retry in 20s.")

    result = provider.generate("hello")

    assert result.ok is False
    assert result.error == "rate_limited"
    assert "rate-limited" in result.text
