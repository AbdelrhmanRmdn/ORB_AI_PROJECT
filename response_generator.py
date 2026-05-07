from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from intent_handler import Intent, IntentHandler
from system_status import format_system_status


@dataclass(frozen=True)
class GeneratedResponse:
    text: str
    intent: Intent
    should_shutdown: bool = False


class ResponseGenerator:
    def __init__(self, intent_handler: IntentHandler | None = None) -> None:
        self.intent_handler = intent_handler or IntentHandler()

    def generate(self, command: str | None, current_user: str | None = None) -> GeneratedResponse:
        intent = self.intent_handler.classify(command)

        if intent.name == "no_input":
            return GeneratedResponse("I did not hear a command.", intent)

        if intent.name == "shutdown":
            return GeneratedResponse("Goodbye.", intent, should_shutdown=True)

        if intent.name == "greeting":
            if current_user:
                return GeneratedResponse(f"Hello {current_user}, how can I help you?", intent)
            return GeneratedResponse("Hello, how can I help you?", intent)

        if intent.name == "current_time":
            return GeneratedResponse(
                f"The current time is {datetime.now().strftime('%I:%M %p')}.",
                intent,
            )

        if intent.name == "current_date":
            return GeneratedResponse(
                f"Today's date is {datetime.now().strftime('%A, %B %d, %Y')}.",
                intent,
            )

        if intent.name == "system_status":
            return GeneratedResponse(format_system_status(), intent)

        if intent.name == "identity":
            if current_user:
                return GeneratedResponse(f"You are {current_user}.", intent)
            return GeneratedResponse("I cannot identify you right now.", intent)

        if intent.name == "assistant_name":
            return GeneratedResponse("I am ORB AI, your offline assistant.", intent)

        if intent.name == "light_control":
            action = intent.slots.get("action", "")
            if action == "on":
                return GeneratedResponse("Turning on the lights.", intent)
            if action == "off":
                return GeneratedResponse("Turning off the lights.", intent)
            return GeneratedResponse("Do you want me to turn the lights on or off?", intent)

        if intent.name == "temperature":
            if intent.slots.get("state") == "hot":
                return GeneratedResponse(
                    "It seems warm. I will turn on the air conditioner.",
                    intent,
                )
            return GeneratedResponse(
                "It seems cool. I will turn off the air conditioner.",
                intent,
            )

        return GeneratedResponse(
            "I heard you, but I am not sure how to help with that yet.",
            intent,
        )


def generate_response(command: str | None, current_user: str | None = None) -> str:
    response = ResponseGenerator().generate(command, current_user=current_user)
    if response.should_shutdown:
        return "shutdown"
    return response.text
