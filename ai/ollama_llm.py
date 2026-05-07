from __future__ import annotations

import json
import urllib.error
import urllib.request

from config import Settings, SETTINGS
from ai.llm_provider import LLMResult
from ai.prompts import ORB_SYSTEM_PROMPT, build_user_prompt
from logging_config import get_logger


logger = get_logger("ai.ollama")


class OllamaLLMProvider:
    provider_name = "ollama"

    def __init__(self, settings: Settings = SETTINGS) -> None:
        self.settings = settings

    def generate(self, prompt: str, current_user: str | None = None) -> LLMResult:
        payload = {
            "model": self.settings.ollama_model,
            "stream": False,
            "prompt": build_user_prompt(prompt, current_user=current_user),
            "system": ORB_SYSTEM_PROMPT,
            "options": {
                "temperature": self.settings.llm_temperature,
                "num_predict": self.settings.llm_max_tokens,
            },
        }
        request = urllib.request.Request(
            f"{self.settings.ollama_host.rstrip('/')}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.settings.llm_timeout_seconds,
            ) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as exc:
            logger.warning("Ollama LLM request failed: %s", exc)
            return LLMResult(
                text="I could not reach the local AI model right now.",
                provider=self.provider_name,
                ok=False,
                error=str(exc),
            )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return LLMResult(
                text="The local AI model returned an invalid response.",
                provider=self.provider_name,
                ok=False,
                error=str(exc),
            )

        text = str(data.get("response", "")).strip()
        if not text:
            return LLMResult(
                text="The local AI model returned an empty answer.",
                provider=self.provider_name,
                ok=False,
                error="empty_response",
            )
        return LLMResult(text=text, provider=self.provider_name, ok=True)
