#!/usr/bin/env python3
"""get-antigravity: Package hub, skip-list manager & distribution synchronizer.

Commands & Flags:
  list / --list             List available packages, versions, categories, and skip status.
  plan / --plan / --check   Preview what packages would be installed or updated.
  apply / --apply / --update Run suite installer to apply pending or selected updates.
  skip <pkg> [--action ...] Add a package to the persistent skip list (~/.gemini/.agy-skip.json).
  unskip <pkg>              Remove a package from the skip list.
  skips / --list-skips      Display active skip list entries.
  status / --status         Show suite health, version drift, and package counts.

Options:
  --only PKG1,PKG2          Filter actions to specific package names.
  --category CAT            Filter actions to a specific category.
  --json                    Output structured JSON instead of human-readable text.
  --no-workspace-sync       Skip workspace git pull during apply/update.
  --dry-run                 Preview apply step without modifying files.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

# Add core module directory to sys.path
BIN_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = BIN_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

import get_antigravity_core as core

SUITE_ROOT = PACKAGE_ROOT.parent.parent
INSTALL_SCRIPT = SUITE_ROOT / "install.py"
REMOTE_TIMEOUT_S = float(os.environ.get("GET_ANTIGRAVITY_REMOTE_TIMEOUT_S", "3.0"))


def _should_skip_remote() -> bool:
    return bool(os.environ.get("GET_ANTIGRAVITY_SKIP_REMOTE_CHECK"))


def fetch_remote_version(pkg_name: str) -> str | None:
    """Fetch published version from upstream GitHub repository."""
    if _should_skip_remote():
        return None
    url = core.package_remote_manifest_url(pkg_name)
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "get-antigravity/1.0"})
        with urllib.request.urlopen(req, timeout=REMOTE_TIMEOUT_S) as response:
            data = json.loads(response.read().decode("utf-8"))
            version = data.get("version")
            return str(version) if version else None
    except Exception:
        return None


def fetch_all_remote_versions(catalog: list[dict]) -> dict[str, str | None]:
    """Fetch remote versions for catalog packages or read from daily cache."""
    stamp_path = core.refresh_stamp_path()
    today_str = core.today()
    
    if _should_skip_remote():
        return {}
    
    # Use cached versions if refreshed today
    if not core.should_refresh(stamp_path, today_str):
        cached = core.load_cached_versions(stamp_path)
        if cached:
            return cached
    
    remote_versions = {}
    for entry in catalog:
        name = entry["name"]
        remote_versions[name] = fetch_remote_version(name)
    
    core.save_refresh_state(stamp_path, today_str, remote_versions)
    return remote_versions


def cmd_list(catalog: list[dict], installed: dict, skip_list: dict, as_json: bool = False) -> int:
    if as_json:
        out = []
        for e in catalog:
            name = e["name"]
            out.append({
                "name": name,
                "version": e.get("version"),
                "category": e.get("category"),
                "installed": name in installed,
                "skip": skip_list.get(name),
                "description": e.get("description"),
                "skills": e.get("skills", []),
                "has_rules": e.get("has_rules", False),
                "has_bin": e.get("has_bin", False),
            })
        print(json.dumps(out, indent=2))
        return 0

    print("==================================================================================")
    print("                    Antigravity Suite - Package Catalog                           ")
    print("==================================================================================")
    header = f"{'Package Name':<28} {'Category':<10} {'Version':<10} {'Installed':<11} {'Skip':<8}"
    print(header)
    print("-" * len(header))
    
    for e in catalog:
        name = e["name"]
        cat = e.get("category", "tools")
        ver = e.get("version", "0.1.0")
        inst = "yes" if name in installed else "no"
        sk = skip_list.get(name, "-")
        print(f"{name:<28} {cat:<10} {ver:<10} {inst:<11} {sk:<8}")
    
    print("-" * len(header))
    print(f"Total: {len(catalog)} packages ({len(installed)} installed, {len(skip_list)} skipped)\n")
    return 0


def cmd_plan(catalog: list[dict], installed: dict, skip_list: dict, only: list[str] | None, category: str | None, as_json: bool = False) -> int:
    remote_versions = fetch_all_remote_versions(catalog)
    plan = core.generate_plan(
        catalog=catalog,
        installed=installed,
        remote_versions=remote_versions,
        skip_list=skip_list,
        names=only,
        category=category,
    )
    
    if as_json:
        print(json.dumps(plan, indent=2))
        return 0
    
    print("==================================================================================")
    print("                    Antigravity Suite - Execution Plan                            ")
    print("==================================================================================")
    
    if not plan["has_actions"]:
        print("[+] All selected packages are installed, current, and up to date.")
        if plan["skipped"]:
            print(f"[*] Skipped packages ({len(plan['skipped'])}):")
            for sk in plan["skipped"]:
                print(f"  - {sk['name']} (skip: {sk['reason']})")
        return 0
    
    if plan["missing"]:
        print(f"[*] Missing packages to install ({len(plan['missing'])}):")
        for name in plan["missing"]:
            print(f"  + {name}")
    
    if plan["outdated"]:
        print(f"[*] Outdated packages to update ({len(plan['outdated'])}):")
        for item in plan["outdated"]:
            print(f"  ^ {item['name']} ({item['installed_version']} -> {item['remote_version']})")
            
    if plan["skipped"]:
        print(f"[*] Skipped packages ({len(plan['skipped'])}):")
        for sk in plan["skipped"]:
            print(f"  ~ {sk['name']} (skip: {sk['reason']})")
            
    print("-" * 82)
    print(f"Ready to apply: {len(plan['missing'])} to install, {len(plan['outdated'])} to update.\n")
    return 0


def cmd_apply(catalog: list[dict], installed: dict, skip_list: dict, only: list[str] | None, category: str | None, no_workspace_sync: bool = False, dry_run: bool = False) -> int:
    if not INSTALL_SCRIPT.is_file():
        print(f"[-] Error: Installer not found at {INSTALL_SCRIPT}", file=sys.stderr)
        return 1
    
    print("[*] Applying Antigravity Suite package installation & sync...")
    cmd = [sys.executable, str(INSTALL_SCRIPT)]
    if no_workspace_sync:
        cmd.append("--no-workspace-sync")
    if dry_run:
        cmd.append("--dry-run")
        
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"[-] Installation encountered an error (exit code {res.returncode})", file=sys.stderr)
        return res.returncode
    
    print("\n[+] Verification:")
    new_installed = core.inspect_installed_packages(catalog)
    for e in core.filter_catalog_by_selection(catalog, names=only, category=category):
        name = e["name"]
        if name in skip_list and skip_list[name] in ("install", "both") and name not in new_installed:
            print(f"  ~ {name}: skipped (configured in skip list)")
        elif name in new_installed:
            print(f"  + {name}: installed ({e.get('version')})")
        else:
            print(f"  ? {name}: uninstalled")
            
    return 0


def cmd_skip(pkg_name: str, action: str = "both") -> int:
    skip_list = core.load_skip_list()
    updated = core.set_skip(skip_list, pkg_name, action=action)
    core.save_skip_list(None, updated)
    print(f"[+] Added '{pkg_name}' to skip list with action: {action}")
    return 0


def cmd_unskip(pkg_name: str) -> int:
    skip_list = core.load_skip_list()
    if pkg_name not in skip_list:
        print(f"[!] '{pkg_name}' was not found in the skip list.")
        return 0
    updated = core.remove_skip(skip_list, pkg_name)
    core.save_skip_list(None, updated)
    print(f"[+] Removed '{pkg_name}' from skip list.")
    return 0


def cmd_list_skips(as_json: bool = False) -> int:
    skip_list = core.load_skip_list()
    if as_json:
        print(json.dumps(skip_list, indent=2))
        return 0
    
    if not skip_list:
        print("[=] Skip list is empty. No packages are skipped.")
        return 0
    
    print("==================================================")
    print("        Antigravity Suite - Skip List             ")
    print("==================================================")
    for pkg, action in sorted(skip_list.items()):
        print(f"  - {pkg:<25} : skip {action}")
    print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="get-antigravity: Package hub & updater for Google Antigravity Suite",
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="subcommand", help="Command to execute")
    
    p_list = subparsers.add_parser("list", help="List available packages")
    p_list.add_argument("--json", action="store_true", help="JSON output")
    
    p_plan = subparsers.add_parser("plan", help="Preview package install/update plan")
    p_plan.add_argument("--only", help="Filter by package names (comma separated)")
    p_plan.add_argument("--category", help="Filter by category")
    p_plan.add_argument("--json", action="store_true", help="JSON output")
    
    p_apply = subparsers.add_parser("apply", help="Execute installation and sync")
    p_apply.add_argument("--only", help="Filter by package names (comma separated)")
    p_apply.add_argument("--category", help="Filter by category")
    p_apply.add_argument("--no-workspace-sync", action="store_true", help="Skip workspace git sync")
    p_apply.add_argument("--dry-run", action="store_true", help="Preview without modifying")
    
    p_skip = subparsers.add_parser("skip", help="Add package to skip list")
    p_skip.add_argument("package", help="Package name to skip")
    p_skip.add_argument("--action", choices=["install", "update", "both"], default="both", help="Action to skip")
    
    p_unskip = subparsers.add_parser("unskip", help="Remove package from skip list")
    p_unskip.add_argument("package", help="Package name to unskip")
    
    p_skips = subparsers.add_parser("skips", help="List all skipped packages")
    p_skips.add_argument("--json", action="store_true", help="JSON output")
    
    p_status = subparsers.add_parser("status", help="Show package status and drift summary")
    p_status.add_argument("--json", action="store_true", help="JSON output")

    # Global flags (for backward-compatibility with older invocations)
    parser.add_argument("--list", action="store_true", help="List available packages")
    parser.add_argument("--plan", "--check", action="store_true", help="Preview updates")
    parser.add_argument("--update", "--apply", action="store_true", help="Apply package updates")
    parser.add_argument("--install", metavar="PKG", help="Install a specific package")
    parser.add_argument("--only", help="Filter by package names")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--list-skips", action="store_true", help="List skip entries")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--no-workspace-sync", action="store_true", help="Skip workspace git sync")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    
    args = parser.parse_args(argv)
    
    catalog = core.load_catalog()
    installed = core.inspect_installed_packages(catalog)
    skip_list = core.load_skip_list()
    
    only_names = [n.strip() for n in args.only.split(",") if n.strip()] if getattr(args, "only", None) else None
    if getattr(args, "install", None):
        only_names = [args.install.strip()]
        
    category = getattr(args, "category", None)
    as_json = getattr(args, "json", False)
    dry_run = getattr(args, "dry_run", False)
    no_ws = getattr(args, "no_workspace_sync", False)

    # Route subcommands or flags
    cmd = args.subcommand
    if cmd == "list" or args.list:
        return cmd_list(core.filter_catalog_by_selection(catalog, names=only_names, category=category), installed, skip_list, as_json=as_json)
    elif cmd == "plan" or args.plan:
        return cmd_plan(catalog, installed, skip_list, only=only_names, category=category, as_json=as_json)
    elif cmd == "skip":
        return cmd_skip(args.package, action=args.action)
    elif cmd == "unskip":
        return cmd_unskip(args.package)
    elif cmd == "skips" or args.list_skips:
        return cmd_list_skips(as_json=as_json)
    elif cmd == "status":
        return cmd_plan(catalog, installed, skip_list, only=only_names, category=category, as_json=as_json)
    elif cmd == "apply" or args.update or args.install:
        return cmd_apply(catalog, installed, skip_list, only=only_names, category=category, no_workspace_sync=no_ws, dry_run=dry_run)
    else:
        # Default behavior: run plan if no args, or apply if explicit
        return cmd_plan(catalog, installed, skip_list, only=only_names, category=category, as_json=as_json)


if __name__ == "__main__":
    sys.exit(main())
