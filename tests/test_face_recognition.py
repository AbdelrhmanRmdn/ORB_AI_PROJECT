from dataclasses import replace

from config import load_settings
from face_rec import FaceRecognizer


def test_mock_face_recognition_returns_authorized_user():
    settings = replace(load_settings(), test_mode=True, mock_user="Karim")
    recognizer = FaceRecognizer(settings)

    identity = recognizer.recognize()

    assert identity.name == "Karim"
    assert identity.authorized is True
    assert identity.reason == "mock"
