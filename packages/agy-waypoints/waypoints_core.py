"""Pure, unit-testable core for the waypoints reminder in Google Antigravity.

Store schema (~/.gemini/waypoints.json, overridable via $WAYPOINTS_FILE):
    {"version": 1, "items": [
        {"id","title","summary","detail","surface_on"(YYYY-MM-DD|null),"created"(YYYY-MM-DD),"done"(bool),"priority"(int)}
    ]}

`surface_on` is the EARLIEST date an item should appear — NOT an expiry.
An item surfaces on and after that date and persists every session until explicitly marked done.
"""
import json
import os
import re
import tempfile
from datetime import date

VERSION = 1
_UNSET = object()


def store_path():
    if os.environ.get("WAYPOINTS_FILE"):
        return os.environ.get("WAYPOINTS_FILE")
    gemini_path = os.path.expanduser("~/.gemini/waypoints.json")
    if os.path.exists(gemini_path):
        return gemini_path
    claude_path = os.path.expanduser("~/.claude/waypoints.json")
    if os.path.exists(claude_path):
        return claude_path
    return gemini_path


def today():
    """Today as YYYY-MM-DD; overridable via $WAYPOINTS_TODAY."""
    return os.environ.get("WAYPOINTS_TODAY") or date.today().isoformat()


def load_store(path=None):
    path = path or store_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict) or not isinstance(d.get("items"), list):
            raise ValueError("bad shape")
        return d
    except FileNotFoundError:
        return {"version": VERSION, "items": []}
    except Exception:
        return {"version": VERSION, "items": []}


def save_store(store, path=None):
    path = path or store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def slugify(title, maxlen=30):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(s) > maxlen:
        cut = s[:maxlen]
        if "-" in cut:
            cut = cut.rsplit("-", 1)[0]
        s = cut.strip("-")
    return s or "item"


def _unique_id(items, base):
    existing = {i.get("id") for i in items}
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"


def add_item(items, title, detail="", surface_on=None, created=None, id=None, summary=None, priority=0):
    item = {
        "id": id or _unique_id(items, slugify(title)),
        "title": title,
        "summary": list(summary) if summary else [],
        "detail": detail or "",
        "surface_on": surface_on,
        "created": created or today(),
        "done": False,
        "priority": priority or 0,
    }
    items.append(item)
    return item


def get_item(items, item_id):
    for i in items:
        if i.get("id") == item_id:
            return i
    return None


def edit_item(items, item_id, title=_UNSET, summary=_UNSET, detail=_UNSET, surface_on=_UNSET, priority=_UNSET):
    it = get_item(items, item_id)
    if it is None:
        return None
    if title is not _UNSET:
        it["title"] = title
    if summary is not _UNSET:
        it["summary"] = list(summary) if summary else []
    if detail is not _UNSET:
        it["detail"] = detail
    if surface_on is not _UNSET:
        it["surface_on"] = surface_on
    if priority is not _UNSET:
        it["priority"] = priority
    return it


def mark_done(items, item_id, outcome=None):
    it = get_item(items, item_id)
    if it is None:
        return None
    it["done"] = True
    if outcome:
        it["title"] = outcome
    return it


def surfaceable_items(items, now_date=None):
    now_date = now_date or today()
    res = []
    for i in items:
        if i.get("done"):
            continue
        soff = i.get("surface_on")
        if soff and soff > now_date:
            continue
        res.append(i)
    # Sort by priority desc, then created date asc
    res.sort(key=lambda x: (-x.get("priority", 0), x.get("created", "")))
    return res


def format_banner(items, now_date=None):
    open_items = surfaceable_items(items, now_date)
    if not open_items:
        return ""
    lines = [
        f"🧭 waypoints: {len(open_items)} open waypoint(s) still ahead — they persist until done. Just ask me to add or complete one:",
    ]
    for it in open_items:
        created = it.get("created", "")
        since_str = f" (since {created})" if created else ""
        lines.append(f"  • {it.get('title')}{since_str}")
        for s in it.get("summary", []):
            lines.append(f"      - {s}")
    return "\n".join(lines)
