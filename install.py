#!/usr/bin/env python3
"""Antigravity Sync - Installer

Sets up antigravity-sync on your local machine (macOS, Windows, or Linux).
Preserves existing host credentials and local settings while merging shared configuration.
"""

import os
import sys
import subprocess
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_PATH = os.path.join(SCRIPT_DIR, "bin", "sync_engine.py")
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "templates", "shared-settings.json")


def main():
    parser = argparse.ArgumentParser(description="Install Antigravity Sync")
    parser.add_argument("--dry-run", action="store_true", help="Preview installation without modifying files")
    args = parser.parse_args()

    print("==================================================")
    print("        Antigravity Sync - Setup & Sync           ")
    print("==================================================")

    if not os.path.isfile(ENGINE_PATH):
        print(f"[-] Error: Sync engine not found at {ENGINE_PATH}", file=sys.stderr)
        sys.exit(1)

    cmd = [sys.executable, ENGINE_PATH, "--template", TEMPLATE_PATH]
    if args.dry_run:
        cmd.append("--dry-run")

    print("[*] Running initial synchronization...")
    res = subprocess.run(cmd)
    
    if res.returncode == 0:
        print("\n[✓] Setup complete!")
        print("To sync your settings at any time, run:")
        print(f"  python3 {ENGINE_PATH}")
    else:
        print("\n[-] Sync encountered an issue. See output above.")
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()
