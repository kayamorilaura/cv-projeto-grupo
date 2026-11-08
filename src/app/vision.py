"""Motion detection, zone assignment and visual overlays."""

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


def zone_for_x(x: int, width: int) -> int:
    """Map a horizontal coordinate to one of the three zones."""
    return min(2, max(0, x * 3 // width))


def group_boxes(
    boxes: list[tuple[int, int, int, int]],
    width: int,
) -> list[list[list[int]]]:
    """Group bounding boxes by the zone containing their center."""
    by_zone: list[list[list[int]]] = [[], [], []]
    for x, y, bw, bh in boxes:
        center_x = x + bw // 2
        zone = zone_for_x(center_x, width)
        by_zone[zone].append([x, y, bw, bh])
    return by_zone


def draw_zone(output: np.ndarray, index: int, name: str, color: tuple[int, int, int]) -> None:
    """Draw a zone boundary and label on the output frame."""
    h, w = output.shape[:2]
    start_x, end_x = index * w // 3, (index + 1) * w // 3
    cv2.rectangle(output, (start_x, 0), (end_x - 1, h - 1), color, 2)
    cv2.putText(
        output,
        f"ZONA {index+1} - {name.upper()}",
        (start_x + 8, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
        cv2.LINE_AA,
    )


def draw_boxes(output: np.ndarray, boxes: list[list[int]], color: tuple[int, int, int]) -> None:
    """Draw motion boxes using the zone's color."""
    for x, y, bw, bh in boxes:
        cv2.rectangle(
            output,
            (x, y),
            (x + bw, y + bh),
            color,
            2,
        )
