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
from datetime import datetime

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

    print(f"[✓] Successfully synced configuration to {cli_path}")

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
                print(f"[✓] Successfully mirrored configuration to Desktop app: {desktop_path}")
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
                print(f"[✓] Synced rule file: {item} -> {dest_file}")


def main():
    parser = argparse.ArgumentParser(description="Antigravity Sync Engine")
    parser.add_argument(
        "--template",
        default=os.path.join(os.path.dirname(__file__), "..", "templates", "shared-settings.json"),
        help="Path to shared settings template JSON",
    )
    parser.add_argument(
        "--rules-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "rules"),
        help="Path to shared rules directory",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    template_path = os.path.abspath(args.template)
    rules_path = os.path.abspath(args.rules_dir)
    
    success = sync_local_config(template_path, dry_run=args.dry_run)
    sync_rules(rules_path, dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
