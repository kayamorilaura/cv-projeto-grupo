"""Map motion bounding boxes to the three visual zones."""

from __future__ import annotations

import cv2
import numpy as np


class ZoneManager:
    def __init__(
        self,
        names: tuple[str, ...],
        colors: tuple[tuple[int, int, int], ...],
    ) -> None:
        self.names = names
        self.colors = colors

    def zone_for_x(self, x: int, width: int) -> int:
        return min(2, max(0, x * 3 // width))

    def group_boxes(
        self,
        boxes: list[tuple[int, int, int, int]],
        width: int,
    ) -> list[list[list[int]]]:
        by_zone: list[list[list[int]]] = [[], [], []]
        for x, y, bw, bh in boxes:
            center_x = x + bw // 2
            zone = self.zone_for_x(center_x, width)
            by_zone[zone].append([x, y, bw, bh])
        return by_zone

    def draw_zone(self, output: np.ndarray, index: int) -> None:
        h, w = output.shape[:2]
        start_x, end_x = index * w // 3, (index + 1) * w // 3
        color = self.colors[index]
        name = self.names[index]
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

    def draw_boxes(self, output: np.ndarray, index: int, boxes: list[list[int]]) -> None:
        for x, y, bw, bh in boxes:
            cv2.rectangle(
                output,
                (x, y),
                (x + bw, y + bh),
                self.colors[index],
                2,
            )
