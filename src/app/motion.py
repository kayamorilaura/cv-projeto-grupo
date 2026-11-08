"""MOG2 foreground extraction and contour filtering."""

from __future__ import annotations

import cv2
import numpy as np


def create_motion_detector():
    """Create the background model and kernel used for motion detection."""
    subtractor = cv2.createBackgroundSubtractorMOG2(
        history=400,
        varThreshold=48,
        detectShadows=True,
    )
    kernel = np.ones((5, 5), np.uint8)
    return subtractor, kernel


def detect_motion(
    frame: np.ndarray, subtractor, kernel: np.ndarray, min_area: int
) -> list[tuple[int, int, int, int]]:
    """Return bounding boxes for contours meeting the minimum area."""
    mask = subtractor.apply(frame)
    # Remove shadows and noise, then connect nearby foreground pixels.
    _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.dilate(mask, kernel, iterations=2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rectangles = []
    for contour in contours:
        if cv2.contourArea(contour) >= min_area:
            rectangles.append(cv2.boundingRect(contour))
    return rectangles
