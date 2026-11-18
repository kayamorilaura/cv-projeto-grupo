"""MP4 recording and timestamped screenshots."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from app.logger import log


def create_recorder(root: Path, folder: Path, fps: float) -> dict:
    """Prepare the timestamped paths and recording state."""
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "root": root,
        "folder": folder,
        "fps": fps,
        "video_path": folder / f"video_{stamp}.mp4",
        "json_path": folder / f"deteccoes_{stamp}.json",
        "writer": None,
    }


def start_recording(recorder: dict, width: int, height: int) -> None:
    """Open the MP4 writer once the frame dimensions are known."""
    if recorder["writer"] is not None:
        return
    writer = cv2.VideoWriter(
        str(recorder["video_path"]),
        cv2.VideoWriter_fourcc(*"mp4v"),
        recorder["fps"],
        (width, height),
    )
    if not writer.isOpened():
        writer.release()
        raise RuntimeError(
            "Não foi possível gravar MP4 (codec mp4v). Verifica OpenCV e a pasta evidencias/."
        )
    recorder["writer"] = writer
    relative_path = recorder["video_path"].relative_to(recorder["root"])
    log(f"Vídeo: {relative_path}", "green")


def write_frame(recorder: dict, frame: np.ndarray) -> None:
    """Append a frame to the open video."""
    if recorder["writer"] is None:
        raise RuntimeError("Recorder is not open")
    recorder["writer"].write(frame)


def save_screenshot(recorder: dict, frame: np.ndarray) -> Path:
    """Save a timestamped PNG and return its path."""
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = recorder["folder"] / f"captura_{stamp}.png"
    cv2.imwrite(str(path), frame)
    log(f"Captura: {path.relative_to(recorder['root'])}", "green")
    return path


def close_recorder(recorder: dict) -> None:
    """Release the video writer if it is open."""
    if recorder["writer"] is not None:
        recorder["writer"].release()
        recorder["writer"] = None
