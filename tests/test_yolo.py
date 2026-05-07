from dataclasses import replace

from config import load_settings
from yolo_detector import YOLOPersonDetector


def test_mock_yolo_person_detection():
    settings = replace(load_settings(), test_mode=True, mock_person_detected=True)
    detector = YOLOPersonDetector(settings)

    detection = detector.detect_person(frame=None)

    assert detection.found is True
    assert detection.confidence == 1.0
