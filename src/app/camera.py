"""Webcam input and mirrored frames."""

from __future__ import annotations

import cv2
import numpy as np


class CameraCapture:
    def __init__(self, index: int) -> None:
        self.index = index
        self.capture: cv2.VideoCapture | None = None

    def open(self) -> None:
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
        self.capture = capture

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self.capture is None:
            raise RuntimeError("Camera is not open")
        ok, frame = self.capture.read()
        if not ok:
            return False, None
        return True, cv2.flip(frame, 1)

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
