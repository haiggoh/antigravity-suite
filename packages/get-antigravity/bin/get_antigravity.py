#!/usr/bin/env python3
"""get-antigravity: Package hub & updater for Antigravity suite.

Features:
  --list                 List available top-level packages.
  --install <pkg>        Run the suite installer (install.py) to sync the specified package.
  --update               Run the suite installer to sync all packages (default behavior).

The script leverages the existing install.py which already handles pulling the latest
commits, syncing shared settings, and performing workspace sync. This wrapper provides
a convenient entry point for users to manage the suite without needing to remember
the full install command.
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
PACKAGES_DIR = SCRIPT_DIR.parent / "packages"
INSTALL_SCRIPT = SCRIPT_DIR.parent / "install.py"

def list_packages():
    pkgs = [p.name for p in PACKAGES_DIR.iterdir() if p.is_dir() and not p.name.startswith('.')]
    print("Available packages:")
    for p in sorted(pkgs):
        print(f" - {p}")
    return pkgs

def install_package(pkg: str):
    if not (PACKAGES_DIR / pkg).is_dir():
        print(f"[!] Package '{pkg}' not found.", file=sys.stderr)
        sys.exit(1)
    cmd = [sys.executable, str(INSTALL_SCRIPT), "--no-workspace-sync"]
    print(f"[+] Running installer for package '{pkg}'...")
    subprocess.run(cmd, check=True)
    print(f"[+] Installation of '{pkg}' completed.")

def main():
    parser = argparse.ArgumentParser(description="get-antigravity package hub & updater.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="List available packages")
    group.add_argument("--install", metavar="PKG", help="Install a specific package")
    group.add_argument("--update", action="store_true", help="Update all packages (default)")
    args = parser.parse_args()
    if args.list:
        list_packages()
    elif args.install:
        install_package(args.install)
    else:
        cmd = [sys.executable, str(INSTALL_SCRIPT)]
        print("[+] Updating entire Antigravity suite...")
        subprocess.run(cmd, check=True)
        print("[+] Suite update completed.")

if __name__ == "__main__":
    main()
