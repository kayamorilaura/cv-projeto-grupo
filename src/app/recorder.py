"""MP4 recording and timestamped screenshots."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from app.logger import AppLogger


class EvidenceRecorder:
    def __init__(self, root: Path, folder: Path, fps: float, logger: AppLogger) -> None:
        self.root = root
        self.folder = folder
        self.fps = fps
        self.logger = logger
        self.folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_path = self.folder / f"video_{stamp}.mp4"
        self.json_path = self.folder / f"deteccoes_{stamp}.json"
        self.writer: cv2.VideoWriter | None = None

    def start_if_needed(self, width: int, height: int) -> None:
        if self.writer is not None:
            return
        writer = cv2.VideoWriter(
            str(self.video_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            self.fps,
            (width, height),
        )
        if not writer.isOpened():
            writer.release()
            raise RuntimeError(
                "Não foi possível gravar MP4 (codec mp4v). Verifica OpenCV e a pasta evidencias/."
            )
        self.writer = writer
        self.logger.info(f"Vídeo: {self.video_path.relative_to(self.root)}", "green")

    def write(self, frame: np.ndarray) -> None:
        if self.writer is None:
            raise RuntimeError("Recorder is not open")
        self.writer.write(frame)

    def screenshot(self, frame: np.ndarray) -> Path:
        path = self.folder / f"captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(str(path), frame)
        self.logger.info(f"Captura: {path.relative_to(self.root)}", "green")
        return path

    def close(self) -> None:
        if self.writer is not None:
            self.writer.release()
            self.writer = None
