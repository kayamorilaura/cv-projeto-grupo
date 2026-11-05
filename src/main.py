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

from app.application import VisualApplication
from app.config import AppConfig


def main() -> None:
    config = AppConfig.from_cli(Path(__file__).resolve().parents[1])
    VisualApplication(config).run()


if __name__ == "__main__":
    main()
