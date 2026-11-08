"""Application configuration and command-line arguments."""

from __future__ import annotations

import argparse
from pathlib import Path


def load_config(root: Path, argv: list[str] | None = None) -> dict:
    """Build the paths, zone settings and command-line options."""
    parser = argparse.ArgumentParser(description="Cena interativa Blender + OpenCV")
    parser.add_argument("--camera", type=int, default=0, help="Índice da webcam (0, 1, ...)")
    parser.add_argument("--min-area", type=int, default=700, help="Área mínima de contorno em px")
    parser.add_argument("--fps", type=float, default=24.0, help="FPS do MP4 gravado")
    parser.add_argument("--warmup", type=int, default=50, help="Frames iniciais para estabilizar MOG2")
    args = parser.parse_args(argv)

    return {
        "root": root,
        "assets_dir": root / "assets",
        "evidence_dir": root / "evidencias",
        "camera_index": args.camera,
        "min_area": args.min_area,
        "fps": args.fps,
        "warmup": args.warmup,
        "hold_seconds": 0.65,
        "zone_sprites": {
            "esquerda": ("chair", "vase"),
            "centro": ("table",),
            "direita": ("dish", "glass"),
        },
        "zone_colors": (
            (255, 180, 60),
            (60, 220, 100),
            (220, 140, 230),
        ),
    }
