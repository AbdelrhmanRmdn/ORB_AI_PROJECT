from dataclasses import replace

from config import load_settings
from speech_to_text import SpeechToText
from text_to_speech import TextToSpeech


def test_mock_speech_to_text_uses_injected_command():
    settings = replace(load_settings(), test_mode=True)
    stt = SpeechToText(settings, mock_command="what time is it")

    assert stt.listen() == "what time is it"


def test_mock_tts_does_not_load_engine():
    settings = replace(load_settings(), test_mode=True)
    tts = TextToSpeech(settings)

    tts.speak("hello", block=True)

    assert tts._engine is None
