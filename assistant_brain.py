from __future__ import annotations

from response_generator import ResponseGenerator, generate_response


__all__ = ["ResponseGenerator", "generate_response"]


if __name__ == "__main__":
    test_commands = [
        "what is your name",
        "system status",
        "what is the time",
        "turn on the lights",
        "turn off the lights",
        "it is cold",
        "it is hot",
        "what is the date",
        "who am i",
        "hello",
        "exit",
    ]

    for cmd in test_commands:
        print(f"Command: {cmd}")
        print(f"Response: {generate_response(cmd, current_user='Karim')}")
        print("-" * 30)
