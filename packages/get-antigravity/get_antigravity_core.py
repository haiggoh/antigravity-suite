"""Pure, unit-testable core for get-antigravity.

No unmockable side-effects live here. Handles:
- Package catalog discovery and metadata inspection (plugin.json / manifests)
- Atomic skip-list persistence (~/.gemini/.agy-skip.json)
- Semantic version comparison and remote drift detection
- Selective package filtering (--only, --category)
- Installation status inspection and execution planning
- Daily refresh stamping and cached version states
"""

import json
import os
import re
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_SUITE_REPO = "https://github.com/haiggoh/antigravity-suite"
DEFAULT_SELF_NAME = "get-antigravity"


def get_home_dir() -> str:
    """Return user's home directory."""
    return os.path.expanduser("~")


def skip_list_path() -> str:
    """Return path to the skip-list JSON file."""
    return os.environ.get("GET_ANTIGRAVITY_SKIP_FILE") or os.environ.get(
        "AGY_SKIP_FILE"
    ) or os.path.join(get_home_dir(), ".gemini", ".agy-skip.json")


def refresh_stamp_path() -> str:
    """Return path to the daily refresh stamp cache file."""
    return os.environ.get("GET_ANTIGRAVITY_REFRESH_STAMP_FILE") or os.path.join(
        get_home_dir(), ".gemini", ".get-antigravity-last-refresh"
    )


def default_packages_dir() -> str:
    """Locate the suite packages/ directory relative to this file or environment."""
    if os.environ.get("AGY_PACKAGES_DIR"):
        return os.environ["AGY_PACKAGES_DIR"]
    
    current = Path(__file__).resolve().parent
    # Check current directory / parent directories for packages/
    for p in [current.parent, current.parent.parent]:
        candidate = p / "packages"
        if candidate.is_dir():
            return str(candidate)
    
    # Fallback to standard AntigravityWorkspace location
    standard = os.path.join(get_home_dir(), "AntigravityWorkspace", "antigravity-suite", "packages")
    return standard


def load_json(path: str) -> Dict[str, Any]:
    """Fail-safe JSON reader: missing, malformed, or unreadable file returns {}."""
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, (dict, list)) else {}
    except Exception:
        return {}


def save_json_atomic(path: str, data: Any) -> None:
    """Atomic JSON write via temporary file and replace to prevent corruption."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    dir_path = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Skip List Management
# ---------------------------------------------------------------------------

def load_skip_list(path: Optional[str] = None) -> Dict[str, str]:
    """Load skip-list dictionary {pkg_name: 'install' | 'update' | 'both'}."""
    target_path = path or skip_list_path()
    data = load_json(target_path)
    if isinstance(data, dict):
        return {str(k): str(v) for k, v in data.items()}
    return {}


def save_skip_list(path: Optional[str], skip_list: Dict[str, str]) -> None:
    """Save skip-list dictionary atomically."""
    target_path = path or skip_list_path()
    save_json_atomic(target_path, skip_list)


def set_skip(skip_list: Dict[str, str], pkg_name: str, action: str = "both") -> Dict[str, str]:
    """Return a updated copy of skip_list with pkg_name set to action."""
    action_norm = action.lower().strip()
    if action_norm not in ("install", "update", "both"):
        action_norm = "both"
    updated = dict(skip_list)
    updated[pkg_name] = action_norm
    return updated


def remove_skip(skip_list: Dict[str, str], pkg_name: str) -> Dict[str, str]:
    """Return an updated copy of skip_list with pkg_name removed."""
    updated = dict(skip_list)
    updated.pop(pkg_name, None)
    return updated


def filter_missing_by_skip(missing: List[str], skip_list: Dict[str, str]) -> List[str]:
    """Filter out missing packages that have 'install' or 'both' in the skip list."""
    return [
        name for name in missing
        if skip_list.get(name) not in ("install", "both")
    ]


def filter_outdated_by_skip(outdated: List[Dict[str, Any]], skip_list: Dict[str, str]) -> List[Dict[str, Any]]:
    """Filter out outdated packages that have 'update' or 'both' in the skip list."""
    return [
        item for item in outdated
        if skip_list.get(item.get("name", "")) not in ("update", "both")
    ]


# ---------------------------------------------------------------------------
# Version Parsing & Semantic Comparison
# ---------------------------------------------------------------------------

def parse_version(text: Optional[str]) -> Optional[Tuple[int, ...]]:
    """Convert dotted semantic version string to comparable integer tuple.
    
    Supports 'v1.2.3', '0.4.0-rc1', '1.0'. Returns None if unparseable.
    """
    if not isinstance(text, str):
        return None
    match = re.fullmatch(r"v?(\d+(?:\.\d+)*)(?:[-+].*)?", text.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def remote_is_newer(installed_version: Optional[str], remote_version: Optional[str]) -> bool:
    """Return True if remote_version is strictly greater than installed_version.
    
    Zero-pads versions of unequal length (e.g. '0.4' equals '0.4.0').
    Returns False when either version is None or empty.
    Falls back to string inequality if version strings cannot be parsed as numeric.
    """
    if not installed_version or not remote_version:
        return False
    left = parse_version(installed_version)
    right = parse_version(remote_version)
    if left is None or right is None:
        return installed_version.strip() != remote_version.strip()
    
    width = max(len(left), len(right))
    left_padded = left + (0,) * (width - len(left))
    right_padded = right + (0,) * (width - len(right))
    return right_padded > left_padded


# ---------------------------------------------------------------------------
# Catalog Discovery & Inspection
# ---------------------------------------------------------------------------

def load_catalog(packages_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Scan packages_dir and extract structured metadata for all suite packages."""
    pkg_root = packages_dir or default_packages_dir()
    if not os.path.isdir(pkg_root):
        return []
    
    entries = []
    for item in sorted(os.listdir(pkg_root)):
        item_path = os.path.join(pkg_root, item)
        if not os.path.isdir(item_path) or item.startswith((".", "_")):
            continue
        
        manifest_path = os.path.join(item_path, "plugin.json")
        manifest = load_json(manifest_path)
        
        # Infer properties if missing from manifest
        name = manifest.get("name") or item
        version = manifest.get("version") or "0.1.0"
        description = manifest.get("description") or f"Antigravity suite module {name}"
        category = manifest.get("category") or ("system" if "sync" in name or "get" in name else "tools")
        author = manifest.get("author") or "haiggoh"
        license_str = manifest.get("license") or "MIT"
        
        # Check components
        has_skills = os.path.isdir(os.path.join(item_path, "skills"))
        has_rules = os.path.isdir(os.path.join(item_path, "rules"))
        has_bin = os.path.isdir(os.path.join(item_path, "bin"))
        
        skills_list = []
        if has_skills:
            sk_dir = os.path.join(item_path, "skills")
            skills_list = [
                s for s in sorted(os.listdir(sk_dir))
                if os.path.isdir(os.path.join(sk_dir, s)) and not s.startswith(".")
            ]
        
        entries.append({
            "name": name,
            "dir_name": item,
            "path": item_path,
            "version": version,
            "description": description,
            "category": category,
            "author": author,
            "license": license_str,
            "has_skills": has_skills,
            "skills": skills_list,
            "has_rules": has_rules,
            "has_bin": has_bin,
        })
    
    return entries


def filter_catalog_by_selection(
    catalog_entries: List[Dict[str, Any]],
    names: Optional[List[str]] = None,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter catalog entries by explicit package names and/or category."""
    out = catalog_entries
    if names:
        wanted = {n.strip() for n in names if n.strip()}
        out = [e for e in out if e["name"] in wanted or e["dir_name"] in wanted]
    if category:
        cat_norm = category.strip().lower()
        out = [e for e in out if e.get("category", "").strip().lower() == cat_norm]
    return out


# ---------------------------------------------------------------------------
# Installation Inspection & State Resolution
# ---------------------------------------------------------------------------

def inspect_installed_packages(
    catalog_entries: List[Dict[str, Any]],
    home_dir: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """Determine which catalog packages are installed in the user's environment.
    
    A package is considered installed if at least one of its declared skills,
    rules, or binaries is deployed to ~/.gemini/ or ~/.local/bin.
    """
    home = home_dir or get_home_dir()
    cli_skills_dir = os.path.join(home, ".gemini", "antigravity-cli", "skills")
    config_skills_dir = os.path.join(home, ".gemini", "config", "skills")
    rules_dir = os.path.join(home, ".gemini", "config", "rules")
    local_bin_dir = os.path.join(home, ".local", "bin")
    
    installed = {}
    for entry in catalog_entries:
        name = entry["name"]
        pkg_path = entry["path"]
        is_installed = False
        
        # 1. Check skills
        for sk in entry.get("skills", []):
            if os.path.isdir(os.path.join(cli_skills_dir, sk)) or os.path.isdir(os.path.join(config_skills_dir, sk)):
                is_installed = True
                break
        
        # 2. Check rules
        if not is_installed and entry.get("has_rules"):
            r_dir = os.path.join(pkg_path, "rules")
            if os.path.isdir(r_dir):
                for rf in os.listdir(r_dir):
                    if rf.endswith(".md") and os.path.isfile(os.path.join(rules_dir, rf)):
                        is_installed = True
                        break
        
        # 3. Check bin
        if not is_installed and entry.get("has_bin"):
            b_dir = os.path.join(pkg_path, "bin")
            if os.path.isdir(b_dir):
                for bf in os.listdir(b_dir):
                    if not bf.startswith((".", "_")) and (
                        os.path.isfile(os.path.join(local_bin_dir, bf)) or
                        os.path.islink(os.path.join(local_bin_dir, bf))
                    ):
                        is_installed = True
                        break

        # 4. Check statusline
        if not is_installed and "statusline" in name:
            status_dir = os.path.join(home, ".gemini", "statusline")
            if os.path.isfile(os.path.join(status_dir, "status.py")):
                is_installed = True
        
        if is_installed:
            installed[name] = {
                "installed": True,
                "version": entry.get("version"),
                "path": pkg_path,
            }
            
    return installed


def compute_missing(
    catalog_entries: List[Dict[str, Any]],
    installed: Dict[str, Dict[str, Any]],
    self_name: str = DEFAULT_SELF_NAME,
) -> List[str]:
    """Return names of catalog packages that are not installed."""
    return [
        e["name"] for e in catalog_entries
        if e["name"] != self_name and e["name"] not in installed
    ]


def compute_outdated(
    catalog_entries: List[Dict[str, Any]],
    installed: Dict[str, Dict[str, Any]],
    remote_versions: Dict[str, Optional[str]],
    self_name: str = DEFAULT_SELF_NAME,
) -> List[Dict[str, Any]]:
    """Return list of installed packages where remote_version is strictly newer."""
    outdated = []
    for e in catalog_entries:
        name = e["name"]
        if name == self_name or name not in installed:
            continue
        
        installed_version = installed[name].get("version")
        remote_ver = remote_versions.get(name)
        if remote_is_newer(installed_version, remote_ver):
            outdated.append({
                "name": name,
                "installed_version": installed_version,
                "remote_version": remote_ver,
            })
    return outdated


# ---------------------------------------------------------------------------
# Remote Manifest Resolution & Refresh State Cache
# ---------------------------------------------------------------------------

def package_remote_manifest_url(pkg_name: str, base_repo: str = DEFAULT_SUITE_REPO) -> Optional[str]:
    """Construct raw GitHub URL for packages/<pkg_name>/plugin.json at HEAD."""
    if not base_repo or not isinstance(base_repo, str):
        return None
    match = re.fullmatch(
        r"(?:https?://(?:www\.)?github\.com/|ssh://git@github\.com/|git@github\.com:)"
        r"([^/]+)/([^/]+?)(?:\.git)?/?",
        base_repo.strip(),
    )
    if not match:
        return None
    owner, repo = match.groups()
    return f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/packages/{pkg_name}/plugin.json"


def today() -> str:
    """Return today as YYYY-MM-DD string."""
    return os.environ.get("GET_ANTIGRAVITY_TODAY") or date.today().isoformat()


def should_refresh(stamp_path: str, today_str: str) -> bool:
    """Return True if refresh stamp is missing or from a prior date."""
    stamped = load_json(stamp_path).get("date")
    return stamped != today_str


def mark_refreshed(stamp_path: str, today_str: str) -> None:
    """Record today's date in the refresh stamp file."""
    save_json_atomic(stamp_path, {"date": today_str})


def save_refresh_state(
    stamp_path: str,
    today_str: str,
    remote_versions: Dict[str, Optional[str]],
) -> None:
    """Cache today's date and fetched remote versions atomically."""
    save_json_atomic(
        stamp_path,
        {"date": today_str, "remote_versions": remote_versions or {}},
    )


def load_cached_versions(stamp_path: str) -> Dict[str, Optional[str]]:
    """Return cached remote versions dictionary from stamp file."""
    cached = load_json(stamp_path).get("remote_versions")
    return cached if isinstance(cached, dict) else {}


# ---------------------------------------------------------------------------
# Planning & Presentation
# ---------------------------------------------------------------------------

def generate_plan(
    catalog: List[Dict[str, Any]],
    installed: Dict[str, Dict[str, Any]],
    remote_versions: Optional[Dict[str, Optional[str]]] = None,
    skip_list: Optional[Dict[str, str]] = None,
    names: Optional[List[str]] = None,
    category: Optional[str] = None,
    self_name: str = DEFAULT_SELF_NAME,
) -> Dict[str, Any]:
    """Generate a full execution plan and drift status for package distribution."""
    skips = skip_list or {}
    remotes = remote_versions or {}
    
    selected_catalog = filter_catalog_by_selection(catalog, names=names, category=category)
    
    all_missing = compute_missing(selected_catalog, installed, self_name=self_name)
    all_outdated = compute_outdated(selected_catalog, installed, remotes, self_name=self_name)
    
    actionable_missing = filter_missing_by_skip(all_missing, skips)
    actionable_outdated = filter_outdated_by_skip(all_outdated, skips)
    
    skipped_items = [
        {"name": e["name"], "reason": skips.get(e["name"])}
        for e in selected_catalog
        if e["name"] in skips
    ]
    
    current_items = [
        e["name"] for e in selected_catalog
        if e["name"] in installed
        and e["name"] not in [o["name"] for o in all_outdated]
    ]
    
    return {
        "catalog_count": len(selected_catalog),
        "installed_count": len(installed),
        "missing": actionable_missing,
        "outdated": actionable_outdated,
        "skipped": skipped_items,
        "current": current_items,
        "has_actions": bool(actionable_missing or actionable_outdated),
    }


def format_nudge(missing: List[str], outdated: List[Dict[str, Any]]) -> str:
    """Format notification banner text for available package updates."""
    if not missing and not outdated:
        return ""
    
    lines = [
        "get-antigravity: new or updated Antigravity suite packages available "
        "(use `/get-antigravity --update` or `get-antigravity apply` to sync):"
    ]
    for name in missing:
        lines.append(f"  + {name} (not installed)")
    for item in outdated:
        lines.append(
            f"  ^ {item['name']} {item['installed_version']} -> "
            f"{item['remote_version']} (update available)"
        )
    return "\n".join(lines)
