#!/usr/bin/env python3
"""Antigravity PreInvocation Hook for agy-waypoints.

Receives Antigravity PreInvocation JSON on stdin:
{
  "conversationId": "...",
  "workspacePaths": [...],
  "invocationNum": 1,
  ...
}

Emits JSON on stdout:
{
  "injectSteps": [
    {
      "ephemeralMessage": "🧭 waypoints: ..."
    }
  ]
}
"""
import json
import os
import sys

# Add project root to sys.path to import waypoints_core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import waypoints_core
except ImportError:
    waypoints_core = None


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    # Check invocationNum - default to 1 if omitted
    invocation_num = payload.get("invocationNum", 1)

    # Only inject banner on the first invocation turn of a session
    if invocation_num != 1 or not waypoints_core:
        print("{}")
        return

    try:
        store = waypoints_core.load_store()
        banner = waypoints_core.format_banner(store.get("items", []))
        if not banner:
            print("{}")
            return

        response = {
            "injectSteps": [
                {
                    "ephemeralMessage": banner
                }
            ]
        }
        print(json.dumps(response, ensure_ascii=False))
    except Exception:
        # Fail safe - print empty JSON object so execution is never blocked
        print("{}")


if __name__ == "__main__":
    main()
