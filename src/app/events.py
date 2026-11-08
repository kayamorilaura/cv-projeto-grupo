"""Motion event lifecycle, timing and atomic JSON persistence."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.logger import AppLogger


def create_event_tracker(
    path: Path,
    video_path: Path,
    root: Path,
    zone_count: int,
    hold_seconds: float,
    logger: AppLogger,
) -> dict:
    """Create the event state for each zone and initialize the JSON file."""
    zones = []
    for _ in range(zone_count):
        zones.append({"event": None, "last_seen": float("-inf"), "last_centroid": None})

    tracker = {
        "path": path,
        "video_path": video_path,
        "root": root,
        "hold_seconds": hold_seconds,
        "logger": logger,
        "events": [],
        "zones": zones,
    }
    write_events(tracker)
    return tracker


def record_motion(
    tracker: dict,
    zone: int,
    zone_name: str,
    boxes: list[list[int]],
    center: tuple[int, int],
    now: float,
    video_seconds: float,
) -> tuple[float, int]:
    """Start or update an event and return animation time and direction."""
    state = tracker["zones"][zone]
    state["last_seen"] = now

    if state["event"] is None:
        state["event"] = {
            "inicio": datetime.now().astimezone().isoformat(timespec="seconds"),
            "duracao_segundos": 0.0,
            "zona": f"{zone+1} - {zone_name}",
            "ficheiro_gravado": tracker["video_path"].relative_to(tracker["root"]).as_posix(),
            "bounding_boxes": [],
            "_start_mono": now,
        }
        tracker["logger"].info(f"Movimento: zona {zone+1} ({zone_name})", "yellow")

    event = state["event"]
    if len(event["bounding_boxes"]) < 25:
        event["bounding_boxes"].append({
            "tempo_video_segundos": round(video_seconds, 2),
            "caixas": boxes[:8],
        })

    direction = 0
    if state["last_centroid"] is not None:
        dx = center[0] - state["last_centroid"][0]
        if dx > 5:
            direction = 1
        elif dx < -5:
            direction = -1
    state["last_centroid"] = center

    return now - event["_start_mono"], direction


def expire_zone(tracker: dict, zone: int, now: float) -> None:
    """End an event after its zone has been inactive for the hold period."""
    state = tracker["zones"][zone]
    if state["event"] is not None and now - state["last_seen"] > tracker["hold_seconds"]:
        end_event(tracker, zone, now)


def end_event(tracker: dict, zone: int, now: float) -> None:
    """Finalize an event, persist it, and clear its zone state."""
    state = tracker["zones"][zone]
    event = state["event"]
    if event is None:
        return

    event["duracao_segundos"] = round(max(0.0, now - event.pop("_start_mono")), 2)
    tracker["events"].append(event)
    write_events(tracker)
    tracker["logger"].info(
        f"Zona {event['zona']}: evento gravado ({event['duracao_segundos']} s)",
        "green",
    )
    state["event"] = None
    state["last_centroid"] = None


def finish_events(tracker: dict, now: float) -> None:
    """Finalize every active event when the application stops."""
    for zone, state in enumerate(tracker["zones"]):
        if state["event"] is not None:
            end_event(tracker, zone, now)


def write_events(tracker: dict) -> None:
    """Replace the JSON file with the current completed-event list."""
    path = tracker["path"]
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(tracker["events"], ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)
