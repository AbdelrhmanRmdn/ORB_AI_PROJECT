from dataclasses import replace

from camera import CameraSource
from config import load_settings


def test_mock_camera_returns_frame():
    settings = replace(load_settings(), test_mode=True)
    camera = CameraSource(settings)

    result = camera.read_frame()

    assert result.ok is True
    assert result.frame is not None
    assert result.frame.shape == (settings.camera_height, settings.camera_width, 3)
