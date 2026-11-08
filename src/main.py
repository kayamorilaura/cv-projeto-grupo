#!uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "numpy",
#   "opencv-python>=5.0,<6",
#   "rich",
# ]
# ///

from pathlib import Path

from app.application import run_application
from app.config import load_config


def main() -> None:
    config = load_config(Path(__file__).resolve().parents[1])
    run_application(config)


if __name__ == "__main__":
    main()
