from __future__ import annotations

from speech_to_text import SpeechToText
from text_to_speech import TextToSpeech


_tts = TextToSpeech()
_stt = SpeechToText()


def speak(text: str) -> None:
    _tts.speak(text)


def listen() -> str | None:
    return _stt.listen()


if __name__ == "__main__":
    print("Testing voice_assistant.py")

    while True:
        cmd = listen()
        print(f"[TEST RESULT] {cmd}")

        if cmd == "exit":
            break

        if cmd:
            speak(f"You said: {cmd}")
