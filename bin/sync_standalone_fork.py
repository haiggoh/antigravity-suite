#!/usr/bin/env python3
"""Sync Standalone Fork Utility

Synchronizes monorepo packages in packages/<name> to their standalone GitHub repositories.
Reads the `standaloneRepo` URL from the package's plugin.json.
"""

import os
import sys
import json
import shutil
import tempfile
import argparse
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGES_DIR = os.path.join(REPO_ROOT, "packages")


def sync_package(pkg_name: str, message: str = "", dry_run: bool = False) -> bool:
    pkg_dir = os.path.join(PACKAGES_DIR, pkg_name)
    if not os.path.isdir(pkg_dir):
        print(f"[-] Package directory not found: {pkg_dir}", file=sys.stderr)
        return False

    plugin_json = os.path.join(pkg_dir, "plugin.json")
    if not os.path.isfile(plugin_json):
        print(f"[-] No plugin.json in {pkg_dir}", file=sys.stderr)
        return False

    with open(plugin_json, "r", encoding="utf-8") as f:
        meta = json.load(f)

    repo_url = meta.get("standaloneRepo")
    if not repo_url:
        print(f"[=] Skipping {pkg_name}: No 'standaloneRepo' defined in plugin.json")
        return True

    print(f"\n[*] Syncing package '{pkg_name}' -> {repo_url}")
    commit_msg = message or f"feat: sync updates from antigravity-suite {pkg_name}"

    temp_dir = tempfile.mkdtemp(prefix=f"agy_fork_{pkg_name}_")
    try:
        # Clone repo
        res = subprocess.run(["git", "clone", repo_url, temp_dir], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[-] Failed to clone {repo_url}: {res.stderr.strip()}", file=sys.stderr)
            return False

        # Copy files from package to temp_dir (excluding .git)
        for item in os.listdir(pkg_dir):
            if item in {".git", "__pycache__"}:
                continue
            src = os.path.join(pkg_dir, item)
            dst = os.path.join(temp_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        # Check git status in cloned repo
        status_out = subprocess.check_output(["git", "-C", temp_dir, "status", "--porcelain"], text=True).strip()
        if not status_out:
            print(f"[=] {pkg_name}: Standalone repo is already up to date.")
            return True

        if dry_run:
            print(f"[*] [dry-run] Would commit and push to {repo_url}:\n{status_out}")
            return True

        # Commit and push
        subprocess.run(["git", "-C", temp_dir, "add", "-A"], check=True)
        subprocess.run(["git", "-C", temp_dir, "commit", "-m", commit_msg], check=True)
        
        # Detect default branch (main or master)
        branch_out = subprocess.check_output(["git", "-C", temp_dir, "branch", "--show-current"], text=True).strip() or "master"
        push_res = subprocess.run(["git", "-C", temp_dir, "push", "origin", branch_out], capture_output=True, text=True)
        if push_res.returncode == 0:
            print(f"[+] Successfully pushed updates to {repo_url} ({branch_out})")
            return True
        else:
            print(f"[-] Push failed: {push_res.stderr.strip()}", file=sys.stderr)
            return False

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Sync Antigravity Suite packages to standalone GitHub repos")
    parser.add_argument("package", nargs="?", help="Name of package to sync (e.g. agy-statusline)")
    parser.add_argument("--all", action="store_true", help="Sync all packages with standalone repos")
    parser.add_argument("-m", "--message", default="", help="Commit message for standalone repo")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync without pushing")
    args = parser.parse_args()

    if not os.path.isdir(PACKAGES_DIR):
        print(f"[-] Packages directory not found: {PACKAGES_DIR}", file=sys.stderr)
        sys.exit(1)

    if args.all or not args.package:
        targets = [d for d in os.listdir(PACKAGES_DIR) if os.path.isdir(os.path.join(PACKAGES_DIR, d))]
        for t in targets:
            sync_package(t, message=args.message, dry_run=args.dry_run)
    else:
        sync_package(args.package, message=args.message, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
