from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class Intent:
    name: str
    confidence: float
    slots: dict[str, str] = field(default_factory=dict)


class IntentHandler:
    """Small deterministic intent layer that is easy to extend on the Pi."""

    def __init__(self) -> None:
        self._patterns: list[tuple[str, float, tuple[str, ...]]] = [
            ("shutdown", 0.98, ("stop", "exit", "quit", "shutdown", "power down")),
            ("current_time", 0.95, ("time", "clock")),
            ("current_date", 0.90, ("date", "day today")),
            ("system_status", 0.95, ("system status", "status", "health", "battery")),
            ("greeting", 0.90, ("hello", "hi", "hey", "good morning", "good evening")),
            ("identity", 0.90, ("who am i", "identify me")),
            ("assistant_name", 0.85, ("your name", "who are you")),
        ]

    def classify(self, text: str | None) -> Intent:
        normalized = self._normalize(text)
        if not normalized:
            return Intent("no_input", 0.0)

        for name, confidence, phrases in self._patterns:
            if any(phrase in normalized for phrase in phrases):
                return Intent(name, confidence)

        if "light" in normalized or "lights" in normalized:
            action = "on" if "on" in normalized else "off" if "off" in normalized else ""
            return Intent("light_control", 0.78, {"action": action})

        if any(word in normalized for word in ("hot", "warm")):
            return Intent("temperature", 0.75, {"state": "hot"})

        if any(word in normalized for word in ("cold", "cool")):
            return Intent("temperature", 0.75, {"state": "cold"})

        return Intent("fallback", 0.2)

    @staticmethod
    def _normalize(text: str | None) -> str:
        if text is None:
            return ""
        lowered = text.lower().strip()
        return re.sub(r"\s+", " ", lowered)
