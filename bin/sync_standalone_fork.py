#!/usr/bin/env python3
"""Bi-directional Standalone Fork & Upstream Sync Utility

Synchronizes monorepo packages in packages/<name> with their standalone GitHub repositories
and upstream original sources.
Reads `standaloneRepo` and `upstream.repository` from the package's plugin.json.

Modes:
  --push           Push changes from packages/<name> to standalone GitHub repo (default)
  --pull           Pull latest changes from standalone GitHub repo into packages/<name>
  --pull-upstream  Fetch latest upstream commits, merge into fork, and update packages/<name>
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


def get_package_meta(pkg_name: str):
    pkg_dir = os.path.join(PACKAGES_DIR, pkg_name)
    plugin_json = os.path.join(pkg_dir, "plugin.json")
    if not os.path.isdir(pkg_dir) or not os.path.isfile(plugin_json):
        return None, None
    try:
        with open(plugin_json, "r", encoding="utf-8") as f:
            return pkg_dir, json.load(f)
    except Exception:
        return pkg_dir, None


def push_package(pkg_name: str, message: str = "", dry_run: bool = False) -> bool:
    """Push local package modifications to standalone fork."""
    pkg_dir, meta = get_package_meta(pkg_name)
    if not meta:
        print(f"[-] No valid plugin.json in {pkg_name}", file=sys.stderr)
        return False

    repo_url = meta.get("standaloneRepo")
    if not repo_url:
        print(f"[=] Skipping {pkg_name}: No 'standaloneRepo' defined in plugin.json")
        return True

    print(f"\n[*] [PUSH] Syncing '{pkg_name}' -> {repo_url}")
    commit_msg = message or f"feat: sync updates from antigravity-suite {pkg_name}"

    temp_dir = tempfile.mkdtemp(prefix=f"agy_push_{pkg_name}_")
    try:
        res = subprocess.run(["git", "clone", repo_url, temp_dir], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[-] Failed to clone {repo_url}: {res.stderr.strip()}", file=sys.stderr)
            return False

        for item in os.listdir(pkg_dir):
            if item in {".git", "__pycache__"}:
                continue
            src = os.path.join(pkg_dir, item)
            dst = os.path.join(temp_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        status_out = subprocess.check_output(["git", "-C", temp_dir, "status", "--porcelain"], text=True).strip()
        if not status_out:
            print(f"  [=] {pkg_name}: Standalone repo is already up to date.")
            return True

        if dry_run:
            print(f"  [*] [dry-run] Would commit and push to {repo_url}:\n{status_out}")
            return True

        subprocess.run(["git", "-C", temp_dir, "add", "-A"], check=True)
        subprocess.run(["git", "-C", temp_dir, "commit", "-m", commit_msg], check=True)
        branch_out = subprocess.check_output(["git", "-C", temp_dir, "branch", "--show-current"], text=True).strip() or "master"
        push_res = subprocess.run(["git", "-C", temp_dir, "push", "origin", branch_out], capture_output=True, text=True)
        if push_res.returncode == 0:
            print(f"  [+] Successfully pushed updates to {repo_url} ({branch_out})")
            return True
        else:
            print(f"  [-] Push failed: {push_res.stderr.strip()}", file=sys.stderr)
            return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def pull_package(pkg_name: str, dry_run: bool = False) -> bool:
    """Pull changes from standalone fork into local package folder."""
    pkg_dir, meta = get_package_meta(pkg_name)
    if not meta:
        print(f"[-] No valid plugin.json in {pkg_name}", file=sys.stderr)
        return False

    repo_url = meta.get("standaloneRepo")
    if not repo_url:
        print(f"[=] Skipping {pkg_name}: No 'standaloneRepo' defined in plugin.json")
        return True

    print(f"\n[*] [PULL] Importing '{pkg_name}' <- {repo_url}")
    temp_dir = tempfile.mkdtemp(prefix=f"agy_pull_{pkg_name}_")
    try:
        res = subprocess.run(["git", "clone", repo_url, temp_dir], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[-] Failed to clone {repo_url}: {res.stderr.strip()}", file=sys.stderr)
            return False

        copied_count = 0
        for item in os.listdir(temp_dir):
            if item in {".git", "__pycache__"}:
                continue
            src = os.path.join(temp_dir, item)
            dst = os.path.join(pkg_dir, item)
            if dry_run:
                print(f"  [*] [dry-run] Would import: {item} -> {dst}")
            else:
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            copied_count += 1

        print(f"  [+] Successfully imported {copied_count} items from {repo_url} into packages/{pkg_name}")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def pull_upstream(pkg_name: str, dry_run: bool = False) -> bool:
    """Fetch updates from original upstream repository, rebase/merge, and sync to suite."""
    pkg_dir, meta = get_package_meta(pkg_name)
    if not meta:
        print(f"[-] No valid plugin.json in {pkg_name}", file=sys.stderr)
        return False

    standalone_url = meta.get("standaloneRepo")
    upstream_info = meta.get("upstream", {})
    upstream_url = upstream_info.get("repository") if isinstance(upstream_info, dict) else None

    if not upstream_url or not standalone_url:
        print(f"[-] Missing upstream.repository or standaloneRepo in {pkg_name}/plugin.json", file=sys.stderr)
        return False

    print(f"\n[*] [UPSTREAM SYNC] Fetching upstream: {upstream_url}")
    temp_dir = tempfile.mkdtemp(prefix=f"agy_upstream_{pkg_name}_")
    try:
        # Clone fork
        subprocess.run(["git", "clone", standalone_url, temp_dir], check=True, capture_output=True)
        # Add upstream remote
        subprocess.run(["git", "-C", temp_dir, "remote", "add", "upstream", upstream_url], check=True)
        subprocess.run(["git", "-C", temp_dir, "fetch", "upstream"], check=True)

        branch_out = subprocess.check_output(["git", "-C", temp_dir, "branch", "--show-current"], text=True).strip() or "master"
        merge_res = subprocess.run(["git", "-C", temp_dir, "merge", f"upstream/{branch_out}", "-m", "chore: merge upstream updates"], capture_output=True, text=True)

        if merge_res.returncode != 0:
            print(f"  [!] Note during upstream merge: {merge_res.stderr.strip() or merge_res.stdout.strip()}")
        else:
            print(f"  [+] Successfully merged upstream/{branch_out} into fork.")

        if not dry_run:
            subprocess.run(["git", "-C", temp_dir, "push", "origin", branch_out], check=False)
            # Copy back to packages/
            for item in os.listdir(temp_dir):
                if item in {".git", "__pycache__"}:
                    continue
                src = os.path.join(temp_dir, item)
                dst = os.path.join(pkg_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            print(f"  [+] Synced latest upstream changes to packages/{pkg_name}")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Bi-directional Standalone Fork & Upstream Sync Utility")
    parser.add_argument("package", nargs="?", help="Name of package to sync (e.g. agy-statusline)")
    parser.add_argument("--all", action="store_true", help="Sync all packages with standalone repos")
    parser.add_argument("--push", action="store_true", help="Push suite package updates to standalone repo (default)")
    parser.add_argument("--pull", action="store_true", help="Pull standalone repo updates into suite package")
    parser.add_argument("--pull-upstream", action="store_true", help="Pull original upstream updates into standalone fork & suite")
    parser.add_argument("-m", "--message", default="", help="Commit message for standalone repo")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing/pushing")
    args = parser.parse_args()

    if not os.path.isdir(PACKAGES_DIR):
        print(f"[-] Packages directory not found: {PACKAGES_DIR}", file=sys.stderr)
        sys.exit(1)

    targets = [args.package] if args.package else [d for d in os.listdir(PACKAGES_DIR) if os.path.isdir(os.path.join(PACKAGES_DIR, d))]

    for t in targets:
        if args.pull_upstream:
            pull_upstream(t, dry_run=args.dry_run)
        elif args.pull:
            pull_package(t, dry_run=args.dry_run)
        else:
            push_package(t, message=args.message, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

