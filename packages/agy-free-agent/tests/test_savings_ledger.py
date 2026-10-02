#!/usr/bin/env python3
"""Tests for the local-offload savings ledger."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "bin", "agy_savings_ledger.py")
spec = importlib.util.spec_from_file_location("sl", SCRIPT)
sl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl)


def run_cli(argv, ledger_dir):
    env = dict(os.environ, AGY_LOCAL_LEDGER_DIR=ledger_dir, LOCAL_AGENTS_LEDGER_DIR=ledger_dir)
    return subprocess.run([sys.executable, SCRIPT] + argv, capture_output=True, text=True, env=env)


class TestSavingsLedger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ledger_dir = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normalize_model(self):
        cases = [
            ("claude-opus-5", "claude-opus-5"),
            ("claude-opus-5[1m]", "claude-opus-5"),
            ("anthropic.claude-opus-5", "claude-opus-5"),
            ("claude-haiku-4-5-20251001", "claude-haiku-4-5"),
            ("claude-opus-4-8-fast", "claude-opus-4-8"),
            ("CLAUDE-OPUS-5", "claude-opus-5"),
            ("  claude-opus-5  ", "claude-opus-5"),
            ("some/route/claude-sonnet-5", "claude-sonnet-5"),
            ("gemini-3.7-flash", "gemini-3.7-flash"),
        ]
        for raw, want in cases:
            self.assertEqual(sl.normalize_model(raw), want)
        self.assertEqual(sl.normalize_model(""), "")
        self.assertEqual(sl.normalize_model(None), "")

    def test_price_honesty_rule(self):
        rates, as_of, label = sl.load_rates()
        saved, rin, rout, src = sl.price("claude-opus-5", 1_000_000, 1_000_000, rates, label)
        self.assertEqual(saved, 30.0)
        self.assertEqual((rin, rout), (5.0, 25.0))
        self.assertIn("builtin", src)

        # Unknown model prices as None, not 0.0
        saved_u, rin_u, rout_u, src_u = sl.price("unknown-model-xyz", 1000, 1000, rates, label)
        self.assertIsNone(saved_u)
        self.assertEqual(src_u, "unknown")

        # Genuinely 0 tokens dispatch
        saved_z, _, _, _ = sl.price("claude-opus-5", 0, 0, rates, label)
        self.assertEqual(saved_z, 0.0)

    def test_record_and_rollup(self):
        r1 = run_cli(["record", "--model", "qwen-3.8-operator", "--in", "10000", "--out", "1000", "--priced-against", "claude-opus-5", "--session", "s1"], self.ledger_dir)
        self.assertEqual(r1.returncode, 0)

        events_file = os.path.join(self.ledger_dir, "savings.jsonl")
        self.assertTrue(os.path.isfile(events_file))

        with open(events_file) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        ev = json.loads(lines[0])
        self.assertEqual(ev["session"], "s1")
        self.assertEqual(ev["input_tokens"], 10000)
        self.assertEqual(ev["output_tokens"], 1000)

        # Rollup
        r_roll = run_cli(["rollup"], self.ledger_dir)
        self.assertEqual(r_roll.returncode, 0)
        rollup_file = os.path.join(self.ledger_dir, "rollup.json")
        self.assertTrue(os.path.isfile(rollup_file))

        # Report
        r_rep = run_cli(["report", "--json"], self.ledger_dir)
        self.assertEqual(r_rep.returncode, 0)
        data = json.loads(r_rep.stdout)
        self.assertEqual(data["events"], 1)
        self.assertGreater(data["saved_usd"], 0)


if __name__ == "__main__":
    unittest.main()
