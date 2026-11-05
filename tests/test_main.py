"""Tests for the application entry point."""

import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.config import AppConfig


class MainTests(unittest.TestCase):
    def test_main_uses_project_root_for_assets_and_evidence(self):
        config = AppConfig(root=ROOT)
        with patch("app.config.AppConfig.from_cli", return_value=config) as from_cli:
            with patch("app.application.VisualApplication") as application:
                runpy.run_path(str(ROOT / "src" / "main.py"), run_name="__main__")

        from_cli.assert_called_once_with(ROOT)
        application.assert_called_once_with(config)
        application.return_value.run.assert_called_once_with()
        self.assertEqual(config.assets_dir, ROOT / "assets")
        self.assertTrue(config.assets_dir.is_dir())
        self.assertEqual(config.evidence_dir, ROOT / "evidencias")


if __name__ == "__main__":
    unittest.main()
