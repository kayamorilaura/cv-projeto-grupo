"""Per-zone object reactions and transparent sprite composition."""

from __future__ import annotations

import cv2
import numpy as np


class AnimationRenderer:
    def __init__(self, assets: dict[str, list[np.ndarray]]) -> None:
        self.assets = assets

    def render_zone(
        self,
        output: np.ndarray,
        zone_index: int,
        objects: tuple[str, ...],
        center: tuple[int, int],
        extent: int,
        direction: int,
        play_time: float,
    ) -> None:
        for obj_index, name in enumerate(objects):
            images = self.assets[name]

            if zone_index == 0:
                if obj_index == 0:
                    position = (center[0] - 40, center[1])
                    side = 145
                else:
                    position = (center[0] + 52, center[1])
                    side = 95
                speed = 24
            elif zone_index == 1:
                position = center
                side = min(235, max(100, int(extent * 0.95)))
                speed = 24
            else:
                if obj_index == 0:
                    position = (center[0] - 38, center[1])
                    side = 135
                else:
                    position = (center[0] + 43, center[1])
                    side = 105
                if direction > 0:
                    speed = 35
                elif direction < 0:
                    speed = 12
                else:
                    speed = 24

            frame_id = int(play_time * speed) % len(images)
            self.overlay_rgba(output, images[frame_id], position, side)

    def overlay_rgba(
        self,
        frame: np.ndarray,
        sprite: np.ndarray,
        center: tuple[int, int],
        side: int,
    ) -> None:
        side = max(40, int(side))
        h0, w0 = sprite.shape[:2]
        dest_w = side
        dest_h = max(1, round(side * h0 / w0))
        image = cv2.resize(sprite, (dest_w, dest_h), interpolation=cv2.INTER_AREA)

        h, w = frame.shape[:2]
        x = round(center[0] - dest_w / 2)
        y = round(center[1] - dest_h / 2)

        xa, ya = max(0, x), max(0, y)
        xb, yb = min(w, x + dest_w), min(h, y + dest_h)
        if xa >= xb or ya >= yb:
            return

        crop = image[ya - y:yb - y, xa - x:xb - x]
        alpha = crop[:, :, 3:4].astype(np.float32) / 255.0
        background = frame[ya:yb, xa:xb].astype(np.float32)
        foreground = crop[:, :, :3].astype(np.float32)
        frame[ya:yb, xa:xb] = np.clip(
            foreground * alpha + background * (1.0 - alpha), 0, 255
        ).astype(np.uint8)
