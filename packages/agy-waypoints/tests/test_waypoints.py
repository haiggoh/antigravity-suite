"""Unit tests for agy-waypoints core logic."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import waypoints_core


class TestWaypointsCore(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.environ["WAYPOINTS_FILE"] = self.tmp.name
        os.environ["WAYPOINTS_TODAY"] = "2026-08-10"

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_add_and_load(self):
        store = waypoints_core.load_store()
        self.assertEqual(len(store["items"]), 0)

        item = waypoints_core.add_item(store["items"], "Fix bug in parser", summary=["key point"])
        waypoints_core.save_store(store)

        loaded = waypoints_core.load_store()
        self.assertEqual(len(loaded["items"]), 1)
        self.assertEqual(loaded["items"][0]["title"], "Fix bug in parser")
        self.assertEqual(loaded["items"][0]["id"], "fix-bug-in-parser")

    def test_banner_formatting(self):
        store = waypoints_core.load_store()
        waypoints_core.add_item(store["items"], "First Waypoint", summary=["step 1"])
        banner = waypoints_core.format_banner(store["items"])
        self.assertIn("🧭 waypoints: 1 open waypoint(s)", banner)
        self.assertIn("First Waypoint", banner)

    def test_mark_done(self):
        store = waypoints_core.load_store()
        item = waypoints_core.add_item(store["items"], "Task to complete")
        waypoints_core.mark_done(store["items"], item["id"], outcome="Completed Task")
        self.assertTrue(item["done"])
        self.assertEqual(item["title"], "Completed Task")
        banner = waypoints_core.format_banner(store["items"])
        self.assertEqual(banner, "")


if __name__ == "__main__":
    unittest.main()
