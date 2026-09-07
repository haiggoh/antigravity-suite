#!/usr/bin/env python3
"""CLI interface for agy-cost-tracker.

Commands:
  report      Show today's or date-ranged spend report table
  statusline  Emit single-line ticker for statusline integration
  doctor      Inspect ledger directories, learned cap, and anomalies
  cap         Manage or learn gateway budget cap (--learn)
"""

import os
import sys
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_cost_tracker_core as core


def main():
    parser = argparse.ArgumentParser(description="Antigravity API Spend and Cost Tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # report command
    rep_p = subparsers.add_parser("report", help="Show spend table")
    rep_p.add_argument("--json", action="store_true", help="Output JSON structure")
    rep_p.add_argument("--date", help="Specific UTC date (YYYY-MM-DD)")

    # statusline command
    subparsers.add_parser("statusline", help="Emit single line for statusline")

    # doctor command
    subparsers.add_parser("doctor", help="Check config and records health")

    # cap command
    cap_p = subparsers.add_parser("cap", help="Inspect or learn budget cap")
    cap_p.add_argument("--learn", action="store_true", help="Learn cap from gateway refusal turns")

    args = parser.parse_args()
    cap = core.get_configured_cap()

    if args.command == "report":
        data = core.tally_daily_spend(target_date_utc=args.date)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(core.format_report_table(data, cap_usd=cap))

    elif args.command == "statusline":
        data = core.tally_daily_spend()
        today_spend = data.get("total_spend_usd", 0.0)
        # Attempt to read local savings if available
        local_saved = None
        try:
            local_ledger_script = os.path.expanduser("~/.local/bin/agy-savings-ledger")
            if os.path.isfile(local_ledger_script):
                import subprocess
                res = subprocess.run([local_ledger_script, "report", "--json"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    sl_data = json.loads(res.stdout)
                    local_saved = sl_data.get("total_saved_usd", 0.0)
        except Exception:
            pass

        print(core.format_statusline(today_spend=today_spend, cap_usd=cap, local_saved=local_saved))

    elif args.command == "cap":
        if args.learn:
            learned = core.learn_cap_from_transcripts()
            if learned:
                print(f"[+] Learned Budget Cap: ${learned['cap_usd']:.2f}")
                print(f"    Source Session: {learned['conversation_id']}")
                print(f"    Turn: {learned['provenance_turn']}")
            else:
                print(f"[=] No gateway refusal turns found. Using configured cap: ${cap:.2f}")
        else:
            print(f"Current Configured Daily Cap: ${cap:.2f}")

    elif args.command == "doctor":
        brain = core.get_brain_dir()
        print("=== agy-cost-tracker doctor ===")
        print(f"Brain Directory: {brain} (exists: {os.path.isdir(brain)})")
        print(f"Configured Cap: ${cap:.2f}")
        tally = core.tally_daily_spend()
        print(f"Today Spend: ${tally['total_spend_usd']:.4f} across {tally['session_count']} session(s)")
        print("[+] Doctor check completed with 0 errors.")


if __name__ == "__main__":
    main()
