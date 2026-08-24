#!/usr/bin/env python3
"""Antigravity Sync Engine

Cross-platform, multi-device, and cross-app configuration synchronizer for Google Antigravity.
Keeps settings, status lines, skills, rules, and MCP servers in sync between macOS & Windows,
and between local CLI and Desktop / IDE applications.
"""

import sys
import os
import json
import shutil
import platform
import argparse
import subprocess
from datetime import datetime

# Ensure stdout and stderr handle utf-8 safely across platforms (e.g. Windows cp1252)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Keys that must remain local to each individual machine/account
LOCAL_EXCLUSIVE_KEYS = {
    "trustedWorkspaces",
    "email",
    "account",
    "tokens",
    "auth",
}


def get_home_dir() -> str:
    """Return normalized absolute path to user home directory."""
    return os.path.expanduser("~")


def get_cli_config_path() -> str:
    """Return path to Antigravity CLI settings file."""
    return os.path.join(get_home_dir(), ".gemini", "antigravity-cli", "settings.json")


def get_desktop_config_path() -> str:
    """Return path to Antigravity Desktop / IDE settings file if present."""
    system = platform.system()
    home = get_home_dir()
    if system == "Darwin":
        return os.path.join(home, "Library", "Application Support", "Antigravity", "settings.json")
    elif system == "Windows":
        appdata = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
        return os.path.join(appdata, "Antigravity", "settings.json")
    else:
        return os.path.join(home, ".config", "Antigravity", "settings.json")


def expand_placeholders(obj, home_dir: str):
    """Recursively replace {HOME} placeholders in strings with actual OS home path."""
    if isinstance(obj, str):
        return obj.replace("{HOME}", home_dir)
    elif isinstance(obj, dict):
        return {k: expand_placeholders(v, home_dir) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [expand_placeholders(item, home_dir) for item in obj]
    return obj


def deep_merge(target: dict, source: dict) -> dict:
    """Deep merge source dict into target dict, preserving target values for LOCAL_EXCLUSIVE_KEYS."""
    result = dict(target)
    for key, value in source.items():
        if key in LOCAL_EXCLUSIVE_KEYS and key in target:
            # Preserve machine-local values
            continue
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = deep_merge(result[key], value)
        elif isinstance(value, list) and key in result and isinstance(result[key], list):
            # Union lists without duplicates
            combined = list(result[key])
            for item in value:
                if item not in combined:
                    combined.append(item)
            result[key] = combined
        else:
            result[key] = value
    return result


def backup_file(path: str) -> str:
    """Create timestamped backup of target configuration file."""
    if not os.path.isfile(path):
        return ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(get_home_dir(), ".antigravity", "backups")
    os.makedirs(backup_dir, exist_ok=True)
    filename = os.path.basename(path)
    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
    shutil.copy2(path, backup_path)
    return backup_path


def sync_local_config(template_path: str, dry_run: bool = False) -> bool:
    """Sync local CLI settings against template while preserving machine-specific keys."""
    home_dir = get_home_dir()
    cli_path = get_cli_config_path()

    if not os.path.isfile(template_path):
        print(f"[-] Template not found: {template_path}", file=sys.stderr)
        return False

    with open(template_path, "r", encoding="utf-8") as f:
        template_raw = json.load(f)

    # Expand cross-platform {HOME} placeholder
    template_data = expand_placeholders(template_raw, home_dir)

    # Adjust python binary command for Windows if needed
    if platform.system() == "Windows":
        if "statusLine" in template_data and isinstance(template_data["statusLine"], dict):
            cmd = template_data["statusLine"].get("command", "")
            if cmd.startswith("python3 "):
                template_data["statusLine"]["command"] = "python " + cmd[8:]

    existing_data = {}
    if os.path.isfile(cli_path):
        try:
            with open(cli_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception as e:
            print(f"[!] Warning: Could not parse existing settings at {cli_path}: {e}")

    merged_data = deep_merge(existing_data, template_data)

    if merged_data == existing_data:
        print("[=] Antigravity configuration is already up to date.")
        return True

    if dry_run:
        print("[*] Dry run mode. Changes that would be applied:")
        print(json.dumps(merged_data, indent=2))
        return True

    # Backup existing configuration
    bk = backup_file(cli_path)
    if bk:
        print(f"[+] Backup created: {bk}")

    os.makedirs(os.path.dirname(cli_path), exist_ok=True)
    tmp_path = cli_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp_path, cli_path)

    print(f"[+] Successfully synced configuration to {cli_path}")

    # Also check if Desktop / IDE config exists and mirror non-exclusive settings
    desktop_path = get_desktop_config_path()
    if os.path.isfile(desktop_path):
        try:
            with open(desktop_path, "r", encoding="utf-8") as f:
                desktop_existing = json.load(f)
            desktop_merged = deep_merge(desktop_existing, template_data)
            if desktop_merged != desktop_existing:
                bk_desk = backup_file(desktop_path)
                dtmp = desktop_path + ".tmp"
                with open(dtmp, "w", encoding="utf-8") as f:
                    json.dump(desktop_merged, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                os.replace(dtmp, desktop_path)
                print(f"[+] Successfully mirrored configuration to Desktop app: {desktop_path}")
        except Exception as e:
            print(f"[!] Desktop sync skipped: {e}")

    return True


def sync_rules(rules_dir: str, dry_run: bool = False) -> None:
    """Sync global rules files to ~/.gemini/config/rules/."""
    if not os.path.isdir(rules_dir):
        return
    dest_dir = os.path.join(get_home_dir(), ".gemini", "config", "rules")
    if not dry_run:
        os.makedirs(dest_dir, exist_ok=True)

    for item in os.listdir(rules_dir):
        src_file = os.path.join(rules_dir, item)
        if os.path.isfile(src_file):
            dest_file = os.path.join(dest_dir, item)
            if dry_run:
                print(f"[*] [dry-run] Would sync rule file: {item} -> {dest_file}")
            else:
                shutil.copy2(src_file, dest_file)
                print(f"[+] Synced rule file: {item} -> {dest_file}")


def sync_statusline(statusline_dir: str, dry_run: bool = False) -> None:
    """Sync status line scripts to ~/.antigravity/."""
    if not os.path.isdir(statusline_dir):
        return
    dest_dir = os.path.join(get_home_dir(), ".antigravity")
    if not dry_run:
        os.makedirs(dest_dir, exist_ok=True)

    for item in os.listdir(statusline_dir):
        src_file = os.path.join(statusline_dir, item)
        if os.path.isfile(src_file) and item.endswith(".py"):
            dest_file = os.path.join(dest_dir, item)
            if dry_run:
                print(f"[*] [dry-run] Would sync statusline script: {item} -> {dest_file}")
            else:
                shutil.copy2(src_file, dest_file)
                if sys.platform != "win32":
                    try:
                        os.chmod(dest_file, 0o755)
                    except Exception:
                        pass
                print(f"[+] Synced statusline script: {item} -> {dest_file}")


def sync_workspace_root(workspace_root: str, repo_root: str, dry_run: bool = False) -> None:
    """Sync workspace-level GEMINI.md and .agents configuration to the parent workspace directory."""
    if not os.path.isdir(workspace_root):
        return

    # 1. Sync workspace GEMINI.md
    gemini_template = os.path.join(repo_root, "templates", "workspace-GEMINI.md")
    if os.path.isfile(gemini_template):
        dest_gemini = os.path.join(workspace_root, "GEMINI.md")
        if dry_run:
            print(f"[*] [dry-run] Would sync workspace guidelines: {dest_gemini}")
        else:
            shutil.copy2(gemini_template, dest_gemini)
            print(f"[+] Synced workspace guidelines: GEMINI.md -> {dest_gemini}")

    # 2. Sync workspace .agents hooks/scripts
    agents_template_dir = os.path.join(repo_root, "templates", "agents")
    if os.path.isdir(agents_template_dir):
        dest_agents = os.path.join(workspace_root, ".agents")
        if dry_run:
            print(f"[*] [dry-run] Would sync workspace agent configuration -> {dest_agents}")
        else:
            os.makedirs(dest_agents, exist_ok=True)
            for root, dirs, files in os.walk(agents_template_dir):
                rel = os.path.relpath(root, agents_template_dir)
                target_root = os.path.join(dest_agents, rel) if rel != "." else dest_agents
                os.makedirs(target_root, exist_ok=True)
                for f in files:
                    src_f = os.path.join(root, f)
                    dst_f = os.path.join(target_root, f)
                    shutil.copy2(src_f, dst_f)
            print(f"[+] Synced workspace agent configuration (.agents/) -> {dest_agents}")


def setup_git_autostash() -> None:
    """Ensure git pull.rebase and rebase.autoStash are safely enabled globally."""
    try:
        subprocess.run(["git", "config", "--global", "pull.rebase", "true"], check=False, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "--global", "rebase.autoStash", "true"], check=False, stdout=subprocess.DEVNULL)
    except Exception:
        pass


def migrate_workspace(repo_root: str, dry_run: bool = False) -> None:
    """Migrate local Windows/macOS layout (projects/ folder and GEMINI.md) into antigravity-suite."""
    print("==================================================")
    print("      Antigravity Suite - Automated Migration     ")
    print("==================================================")
    
    parent_dir = os.path.dirname(repo_root)
    packages_dir = os.path.join(repo_root, "packages")
    rules_dest_dir = os.path.join(get_home_dir(), ".gemini", "config", "rules")
    suite_rules_dir = os.path.join(repo_root, "rules")

    # 1. Check for legacy 'projects' folder in parent workspace
    projects_dir = os.path.join(parent_dir, "projects")
    if os.path.isdir(projects_dir):
        if not dry_run:
            os.makedirs(packages_dir, exist_ok=True)
        items = os.listdir(projects_dir)
        print(f"[*] Found legacy projects folder at: {projects_dir} ({len(items)} items)")
        for item in items:
            src = os.path.join(projects_dir, item)
            dst = os.path.join(packages_dir, item)
            if dry_run:
                print(f"[*] [dry-run] Would move: {src} -> {dst}")
            else:
                if os.path.exists(dst):
                    print(f"[!] Target already exists, skipping: {dst}")
                else:
                    shutil.move(src, dst)
                    print(f"[+] Migrated package: {item} -> {dst}")
        if not dry_run and not os.listdir(projects_dir):
            try:
                os.rmdir(projects_dir)
                print(f"[+] Removed empty legacy projects folder: {projects_dir}")
            except Exception:
                pass
    else:
        print("[=] No legacy 'projects' directory found in workspace root.")

    # 2. Check for root GEMINI.md in parent workspace
    parent_gemini_md = os.path.join(parent_dir, "GEMINI.md")
    if os.path.isfile(parent_gemini_md):
        print(f"[*] Found root GEMINI.md at: {parent_gemini_md}")
        global_rule_target = os.path.join(rules_dest_dir, "user_global.md")
        suite_rule_target = os.path.join(suite_rules_dir, "user_global.md")
        if dry_run:
            print(f"[*] [dry-run] Would copy: {parent_gemini_md} -> {global_rule_target}")
            print(f"[*] [dry-run] Would backup: {parent_gemini_md} -> {suite_rule_target}")
        else:
            os.makedirs(rules_dest_dir, exist_ok=True)
            os.makedirs(suite_rules_dir, exist_ok=True)
            shutil.copy2(parent_gemini_md, global_rule_target)
            shutil.copy2(parent_gemini_md, suite_rule_target)
            print(f"[+] Migrated global rules: {parent_gemini_md} -> {global_rule_target}")
            print(f"[+] Backed up rules to suite: {suite_rule_target}")
            bak_path = parent_gemini_md + ".migrated.bak"
            shutil.move(parent_gemini_md, bak_path)
            print(f"[+] Archived original root file: {bak_path}")

    # 3. Update Git remote if still pointing to old repo name
    try:
        rem_out = subprocess.check_output(["git", "-C", repo_root, "remote", "get-url", "origin"], text=True, stderr=subprocess.DEVNULL).strip()
        if "antigravity-sync" in rem_out:
            new_url = rem_out.replace("antigravity-sync", "antigravity-suite")
            if not dry_run:
                subprocess.run(["git", "-C", repo_root, "remote", "set-url", "origin", new_url], check=False)
                print(f"[+] Updated remote URL: {rem_out} -> {new_url}")
    except Exception:
        pass

    # 4. Setup Git autostash
    if not dry_run:
        setup_git_autostash()
        print("[+] Configured global Git pull.rebase and rebase.autoStash = true")

    print("\n[+] Migration complete!\n")


def sync_workspace_repos(workspace_root: str, dry_run: bool = False) -> None:
    """Safe batch pull/rebase with autostash across all workspace git repositories."""
    print("==================================================")
    print("        Antigravity Suite - Workspace Sync        ")
    print("==================================================")

    if not os.path.isdir(workspace_root):
        print(f"[-] Workspace root not found: {workspace_root}", file=sys.stderr)
        return

    setup_git_autostash()

    repos_found = []
    # Check workspace root itself
    if os.path.isdir(os.path.join(workspace_root, ".git")):
        repos_found.append(workspace_root)

    # Check immediate children
    for item in os.listdir(workspace_root):
        sub = os.path.join(workspace_root, item)
        if os.path.isdir(os.path.join(sub, ".git")):
            repos_found.append(sub)

    if not repos_found:
        print(f"[-] No git repositories found in {workspace_root}")
        return

    print(f"[*] Found {len(repos_found)} repositories to synchronize:\n")

    for repo in repos_found:
        repo_name = os.path.basename(repo)
        try:
            status_out = subprocess.check_output(["git", "-C", repo, "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL)
            is_dirty = bool(status_out.strip())
            dirty_tag = " (dirty: autostash active)" if is_dirty else ""

            if dry_run:
                print(f"[*] [dry-run] Would sync {repo_name}{dirty_tag}")
                continue

            # Run git pull --rebase --autostash
            res = subprocess.run(
                ["git", "-C", repo, "pull", "--rebase", "--autostash"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            out = res.stdout.strip()
            if "Already up to date" in out:
                print(f"  [=] {repo_name:25} : Up to date")
            elif res.returncode == 0:
                print(f"  [+] {repo_name:25} : Pulled latest updates{dirty_tag}")
            else:
                print(f"  [!] {repo_name:25} : Sync note - {res.stderr.strip() or out}")
        except Exception as e:
            print(f"  [!] {repo_name:25} : Error: {e}")

    print("\n[+] Workspace repositories sync complete.\n")


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parent_workspace = os.path.dirname(repo_root)

    parser = argparse.ArgumentParser(description="Antigravity Suite & Sync Engine")
    parser.add_argument(
        "--template",
        default=os.path.join(repo_root, "templates", "shared-settings.json"),
        help="Path to shared settings template JSON",
    )
    parser.add_argument(
        "--rules-dir",
        default=os.path.join(repo_root, "rules"),
        help="Path to shared rules directory",
    )
    parser.add_argument(
        "--statusline-dir",
        default=os.path.join(repo_root, "statusline"),
        help="Path to statusline scripts directory",
    )
    parser.add_argument(
        "--workspace-sync",
        action="store_true",
        help="Perform safe multi-repo workspace git pull --rebase --autostash",
    )
    parser.add_argument(
        "--workspace-dir",
        default=parent_workspace,
        help="Path to workspace root directory for --workspace-sync",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Automatically migrate Windows/macOS legacy projects folder & GEMINI.md into suite",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    if args.migrate:
        migrate_workspace(repo_root, dry_run=args.dry_run)

    if args.workspace_sync:
        sync_workspace_repos(os.path.abspath(args.workspace_dir), dry_run=args.dry_run)

    template_path = os.path.abspath(args.template)
    rules_path = os.path.abspath(args.rules_dir)
    statusline_path = os.path.abspath(args.statusline_dir)
    
    success = sync_local_config(template_path, dry_run=args.dry_run)
    sync_rules(rules_path, dry_run=args.dry_run)
    sync_statusline(statusline_path, dry_run=args.dry_run)
    sync_workspace_root(os.path.abspath(args.workspace_dir), repo_root, dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
