
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from app.logger import log


def create_recorder(root: Path, folder: Path, fps: float) -> dict:
    """Prepara a pasta e os nomes dos ficheiros."""

    folder.mkdir(parents=True, exist_ok=True)

    # Cria uma identificação com data e hora
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return {
        "root": root,
        "folder": folder,
        "fps": fps,
        "video_path": folder / f"video_{stamp}.mp4",
        "json_path": folder / f"deteccoes_{stamp}.json",
        "writer": None, # Vídeo ainda não iniciado
    }


def start_recording(recorder: dict, width: int, height: int) -> None:
    """Abre o ficheiro de vídeo."""

    # Evita iniciar a gravação duas vezes
    if recorder["writer"] is not None:
        return

    writer = cv2.VideoWriter(
        str(recorder["video_path"]),
        cv2.VideoWriter_fourcc(*"mp4v"), # Codec de vídeo
        recorder["fps"],                 # Frames por segundo
        (width, height),                 # Resolução
    )

    if not writer.isOpened():
        writer.release()
        raise RuntimeError(
            "Não foi possível gravar MP4 (codec mp4v). "
            "Verifica OpenCV e a pasta evidencias/."
        )

    recorder["writer"] = writer

    relative_path = (
        recorder["video_path"].relative_to(recorder["root"])
    )
    log(f"Vídeo: {relative_path}", "green")


def write_frame(recorder: dict, frame: np.ndarray) -> None:
    """Adiciona um frame ao vídeo."""

    if recorder["writer"] is None:
        raise RuntimeError("Recorder is not open")

    recorder["writer"].write(frame)


def save_screenshot(recorder: dict, frame: np.ndarray) -> Path:
    """Guarda uma captura em PNG."""

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = recorder["folder"] / f"captura_{stamp}.png"

    cv2.imwrite(str(path), frame)

    log(
        f"Captura: {path.relative_to(recorder['root'])}",
        "green",
    )
    return path


def close_recorder(recorder: dict) -> None:
    """Fecha o ficheiro de vídeo corretamente."""

    if recorder["writer"] is not None:
        recorder["writer"].release()
        recorder["writer"] = None
