"""Load RGBA animation sequences once at startup."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.logger import AppLogger


def load_animations(
    folder: Path,
    zone_sprites: dict[str, tuple[str, ...]],
    logger: AppLogger,
) -> dict[str, list[np.ndarray]]:
    """Load sorted four-channel frames for each configured object."""
    animations: dict[str, list[np.ndarray]] = {}
    names: list[str] = []
    for objects in zone_sprites.values():
        for name in objects:
            if name not in names:
                names.append(name)

    for name in names:
        object_folder = folder / name
        paths = sorted(object_folder.glob("*.png"))
        if not paths:
            raise FileNotFoundError(f"Sem PNGs em {object_folder}. Corre 'git pull' na raiz.")

        frames: list[np.ndarray] = []
        for path in paths:
            image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if image is None or image.ndim != 3 or image.shape[2] != 4:
                raise ValueError(f"PNG sem canal alfa RGBA válido: {path}")
            frames.append(image)

        animations[name] = frames
        logger.info(f"{name}: {len(frames)} frames RGBA")

    return animations
