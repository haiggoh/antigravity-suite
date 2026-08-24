#!/usr/bin/env python3
"""Antigravity Sync - Installer

Sets up antigravity-sync on your local machine (macOS, Windows, or Linux).
Preserves existing host credentials and local settings while merging shared configuration.
"""

import os
import sys
import subprocess
import argparse

# Ensure stdout and stderr handle utf-8 safely across platforms (e.g. Windows cp1252)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
        py_cmd = "python" if sys.platform == "win32" else "python3"
        print("\n[+] Setup complete!")
        print("To sync your settings at any time, run:")
        print(f"  {py_cmd} {ENGINE_PATH}")
    else:
        print("\n[-] Sync encountered an issue. See output above.")
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()
