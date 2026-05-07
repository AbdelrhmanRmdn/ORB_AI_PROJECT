import os

import pytest

from config import load_settings


pytestmark = pytest.mark.hardware


@pytest.mark.skipif(
    os.getenv("ORB_RUN_HARDWARE_TESTS") != "1",
    reason="Set ORB_RUN_HARDWARE_TESTS=1 on Raspberry Pi to run hardware smoke tests.",
)
def test_real_camera_smoke():
    from dataclasses import replace
    from camera import CameraSource

    settings = replace(load_settings(), test_mode=False)
    with CameraSource(settings) as camera:
        result = camera.read_frame()

    assert result.ok is True
    assert result.frame is not None
