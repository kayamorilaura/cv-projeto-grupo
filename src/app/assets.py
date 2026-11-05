"""Load RGBA animation sequences once at startup."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.logger import AppLogger


class AssetLoader:
    """Load each configured object's PNG sequence into memory."""

    def __init__(
        self,
        folder: Path,
        zone_sprites: dict[str, tuple[str, ...]],
        logger: AppLogger,
    ) -> None:
        self.folder = folder
        self.zone_sprites = zone_sprites
        self.logger = logger

    def load(self) -> dict[str, list[np.ndarray]]:
        """Return sorted four-channel frames grouped by object name."""
        animations: dict[str, list[np.ndarray]] = {}

        # Preserve object order while avoiding duplicate loads across zones.
        for name in dict.fromkeys(n for group in self.zone_sprites.values() for n in group):
            folder = self.folder / name
            paths = sorted(folder.glob("*.png"))
            if not paths:
                raise FileNotFoundError(f"Sem PNGs em {folder}. Corre 'git pull' na raiz.")

            frames: list[np.ndarray] = []
            for path in paths:
                image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
                if image is None or image.ndim != 3 or image.shape[2] != 4:
                    raise ValueError(f"PNG sem canal alfa RGBA válido: {path}")
                frames.append(image)

            animations[name] = frames
            self.logger.info(f"{name}: {len(frames)} frames RGBA")

        return animations
