#!/usr/bin/env python3
"""Focused tests for the AGY Ornith default picker."""

import contextlib
import io
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch


PACKAGE = Path(__file__).resolve().parents[1]
BIN = PACKAGE / "bin"
CLI_PATH = BIN / "agy_local_delegate.py"
LAUNCHER_PATH = BIN / "agy-local-mode"

if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))

import agy_local_delegate_core as core


class OrnithDefaultPickerTests(unittest.TestCase):
    def test_ornith_is_the_unique_catalog_default(self):
        defaults = [
            alias
            for alias, info in core.MODEL_CATALOG.items()
            if info.get("is_default")
        ]

        self.assertEqual(defaults, ["ornith-1.5-35b"])
        self.assertEqual(
            next(iter(core.MODEL_CATALOG)),
            "ornith-1.5-35b",
        )

        info = core.MODEL_CATALOG["ornith-1.5-35b"]

        self.assertEqual(
            info["default_model_id"],
            "ornith-ai/Ornith-1.5-35B-A3B-MLX-4bit",
        )
        self.assertEqual(
            info["subdir"],
            "Ornith-1.5-35B-A3B-MLX-4bit",
        )
        self.assertEqual(info["context_window"], 262144)

        self.assertFalse(
            core.MODEL_CATALOG["qwen-3.8-operator"].get(
                "is_default",
                False,
            )
        )

    def test_ornith_resolves_to_installed_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            models_dir = Path(temporary)
            model_dir = (
                models_dir / "Ornith-1.5-35B-A3B-MLX-4bit"
            )
            model_dir.mkdir()

            resolved = core.resolve_model_reference(
                "ornith-1.5-35b",
                models_dir=str(models_dir),
            )

            self.assertTrue(resolved["installed"])
            self.assertEqual(
                resolved["local_path"],
                str(model_dir),
            )
            self.assertEqual(
                resolved["serve_arg"],
                str(model_dir),
            )

    def test_blank_menu_selection_returns_ornith_only(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        scan_result = {
            "models_dir": "/tmp/models",
            "exists": True,
            "installed_catalog": [
                {
                    "alias": "ornith-1.5-35b",
                    "description": "Ornith",
                    "subdir": "Ornith-1.5-35B-A3B-MLX-4bit",
                    "size_gb": 19.5,
                }
            ],
            "unregistered_models": [],
        }

        with patch.object(
            sys,
            "argv",
            [str(CLI_PATH), "menu"],
        ), patch.object(
            sys,
            "stdin",
            io.StringIO("\n"),
        ), patch.object(
            core,
            "scan_local_models_dir",
            return_value=scan_result,
        ), patch.object(
            core,
            "find_active_model_servers",
            return_value=[],
        ), contextlib.redirect_stdout(
            stdout
        ), contextlib.redirect_stderr(
            stderr
        ):
            with self.assertRaises(SystemExit) as outcome:
                runpy.run_path(str(CLI_PATH), run_name="__main__")

        self.assertEqual(outcome.exception.code, 0)
        self.assertEqual(
            stdout.getvalue().strip(),
            "ornith-1.5-35b",
        )
        self.assertIn(
            "1) ornith-1.5-35b",
            stderr.getvalue(),
        )
        self.assertIn("(Default)", stderr.getvalue())
        self.assertIn("Selection [1]:", stderr.getvalue())

    def test_local_mode_routes_missing_model_to_picker(self):
        text = LAUNCHER_PATH.read_text(encoding="utf-8")

        self.assertIn(
            'LOCAL_MODEL="${AGY_LOCAL_MODEL_ID:-}"',
            text,
        )
        self.assertIn(
            'if [[ "$FORCE_MENU" -eq 1 || -z "$LOCAL_MODEL" ]]; then',
            text,
        )
        self.assertIn(
            'CHOSEN_MODEL=$(python3 "$DELEGATE_SCRIPT" menu)',
            text,
        )
        self.assertNotIn(
            "AGY_LOCAL_MODEL_ID:-ornith-1.5-35b",
            text,
        )
        self.assertNotIn(
            "AGY_LOCAL_MODEL_ID:-qwen-3.8-operator",
            text,
        )

    def test_explicit_model_argument_remains_supported(self):
        text = LAUNCHER_PATH.read_text(encoding="utf-8")

        self.assertIn(
            '--model) need_value "$@"; LOCAL_MODEL="$2"; shift 2 ;;',
            text,
        )


if __name__ == "__main__":
    unittest.main()
