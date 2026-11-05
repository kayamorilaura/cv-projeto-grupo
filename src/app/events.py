"""Motion event lifecycle, timing and atomic JSON persistence."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.logger import AppLogger


class EventTracker:
    def __init__(
        self,
        path: Path,
        video_path: Path,
        root: Path,
        zone_count: int,
        hold_seconds: float,
        logger: AppLogger,
    ) -> None:
        self.path = path
        self.video_path = video_path
        self.root = root
        self.hold_seconds = hold_seconds
        self.logger = logger
        self.events: list[dict] = []
        self.active: list[dict | None] = [None] * zone_count
        self.last_seen = [float("-inf")] * zone_count
        self.last_centroid: list[tuple[int, int] | None] = [None] * zone_count
        self._write_events()

    def record_motion(
        self,
        zone: int,
        zone_name: str,
        boxes: list[list[int]],
        center: tuple[int, int],
        now: float,
        video_seconds: float,
    ) -> tuple[float, int]:
        self.last_seen[zone] = now

        if self.active[zone] is None:
            self.active[zone] = {
                "inicio": datetime.now().astimezone().isoformat(timespec="seconds"),
                "duracao_segundos": 0.0,
                "zona": f"{zone+1} - {zone_name}",
                "ficheiro_gravado": str(self.video_path.relative_to(self.root)).replace("\\", "/"),
                "bounding_boxes": [],
                "_start_mono": now,
            }
            self.logger.info(f"Movimento: zona {zone+1} ({zone_name})", "yellow")

        event = self.active[zone]
        if len(event["bounding_boxes"]) < 25:
            event["bounding_boxes"].append({
                "tempo_video_segundos": round(video_seconds, 2),
                "caixas": boxes[:8],
            })

        direction = 0
        if self.last_centroid[zone] is not None:
            dx = center[0] - self.last_centroid[zone][0]
            if dx > 5:
                direction = 1
            elif dx < -5:
                direction = -1
            else:
                direction = 0
        self.last_centroid[zone] = center

        play_time = now - event["_start_mono"]
        return play_time, direction

    def expire_zone(self, zone: int, now: float) -> None:
        if self.active[zone] is not None and now - self.last_seen[zone] > self.hold_seconds:
            self.end_event(zone, now)

    def end_event(self, zone: int, now: float) -> None:
        event = self.active[zone]
        if event is None:
            return

        event["duracao_segundos"] = round(max(0.0, now - event.pop("_start_mono")), 2)
        self.events.append(event)
        self._write_events()
        self.logger.info(
            f"Zona {event['zona']}: evento gravado ({event['duracao_segundos']} s)",
            "green",
        )
        self.active[zone] = None
        self.last_centroid[zone] = None

    def finish(self, now: float) -> None:
        for zone in range(len(self.active)):
            if self.active[zone] is not None:
                self.end_event(zone, now)

    def _write_events(self) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.events, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)
