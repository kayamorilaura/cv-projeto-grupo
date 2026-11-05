"""Application configuration and command-line arguments."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    root: Path
    camera_index: int = 0
    min_area: int = 700
    fps: float = 24.0
    warmup: int = 50
    hold_seconds: float = 0.65
    zone_sprites: dict[str, tuple[str, ...]] = field(default_factory=lambda: {
        "esquerda": ("chair", "vase"),
        "centro": ("table",),
        "direita": ("dish", "glass"),
    })
    zone_colors: tuple[tuple[int, int, int], ...] = (
        (255, 180, 60),
        (60, 220, 100),
        (220, 140, 230),
    )

    @property
    def assets_dir(self) -> Path:
        return self.root / "assets"

    @property
    def evidence_dir(self) -> Path:
        return self.root / "evidencias"

    @classmethod
    def from_cli(cls, root: Path, argv: list[str] | None = None) -> AppConfig:
        parser = argparse.ArgumentParser(description="Cena interativa Blender + OpenCV")
        parser.add_argument("--camera", type=int, default=0, help="Índice da webcam (0, 1, ...)")
        parser.add_argument("--min-area", type=int, default=700, help="Área mínima de contorno em px²")
        parser.add_argument("--fps", type=float, default=24.0, help="FPS do MP4 gravado")
        parser.add_argument("--warmup", type=int, default=50, help="Frames iniciais para estabilizar MOG2")
        args = parser.parse_args(argv)
        return cls(
            root=root,
            camera_index=args.camera,
            min_area=args.min_area,
            fps=args.fps,
            warmup=args.warmup,
        )
