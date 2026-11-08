"""Webcam input and mirrored frames."""

from __future__ import annotations

import cv2
import numpy as np


def open_camera(index: int) -> cv2.VideoCapture:
    """Open the webcam with a fallback backend and request a frame size."""
    if hasattr(cv2, "CAP_DSHOW"):
        capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    else:
        capture = cv2.VideoCapture(index)
    if not capture.isOpened():
        capture.release()
        capture = cv2.VideoCapture(index)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"Webcam {index} indisponível. Experimenta --camera 1.")
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
    return capture


def read_camera(capture: cv2.VideoCapture) -> tuple[bool, np.ndarray | None]:
    """Read and mirror a frame, or report an unsuccessful capture."""
    if capture is None:
        raise RuntimeError("Camera is not open")
    ok, frame = capture.read()
    if not ok:
        return False, None
    return True, cv2.flip(frame, 1)
