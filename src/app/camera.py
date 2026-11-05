"""Webcam input and mirrored frames."""

from __future__ import annotations

import cv2
import numpy as np


class CameraCapture:
    """Manage the webcam and return horizontally mirrored frames."""

    def __init__(self, index: int) -> None:
        self.index = index
        self.capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        """Open the webcam with a fallback backend and request a frame size."""
        if hasattr(cv2, "CAP_DSHOW"):
            capture = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        else:
            capture = cv2.VideoCapture(self.index)
        if not capture.isOpened():
            capture.release()
            capture = cv2.VideoCapture(self.index)
        if not capture.isOpened():
            capture.release()
            raise RuntimeError(f"Webcam {self.index} indisponível. Experimenta --camera 1.")
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
        self.capture = capture

    def read(self) -> tuple[bool, np.ndarray | None]:
        """Read and mirror a frame, or report an unsuccessful capture."""
        if self.capture is None:
            raise RuntimeError("Camera is not open")
        ok, frame = self.capture.read()
        if not ok:
            return False, None
        return True, cv2.flip(frame, 1)

    def release(self) -> None:
        """Release the webcam if it is open."""
        if self.capture is not None:
            self.capture.release()
            self.capture = None
