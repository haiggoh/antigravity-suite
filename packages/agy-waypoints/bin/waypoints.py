#!/usr/bin/env python3
"""CLI utility for managing waypoints store (~/.gemini/waypoints.json).

Usage:
  waypoints.py list
  waypoints.py add "Title" [--point "key point"] [--detail "full description"] [--surface-on YYYY-MM-DD] [--priority N]
  waypoints.py edit <id> [--title "New Title"] [--point "new point"] [--detail "new detail"] [--surface-on YYYY-MM-DD]
  waypoints.py show <id>
  waypoints.py done <id> [--as "Resolution outcome"]
  waypoints.py reopen <id>
  waypoints.py toggle <id>
  waypoints.py priority <id> <level>
  waypoints.py prune
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import waypoints_core


def cmd_list(args):
    store = waypoints_core.load_store()
    items = store.get("items", [])
    if not items:
        print("No waypoints found.")
        return
    banner = waypoints_core.format_banner(items)
    if banner:
        print(banner)
    else:
        print("No open waypoints currently surfaceable.")


def cmd_add(args):
    store = waypoints_core.load_store()
    item = waypoints_core.add_item(
        store["items"],
        title=args.title,
        detail=args.detail,
        surface_on=args.surface_on,
        summary=args.point,
        priority=args.priority,
    )
    waypoints_core.save_store(store)
    print(f"Added waypoint [{item['id']}]: {item['title']}")


def cmd_edit(args):
    store = waypoints_core.load_store()
    kw = {}
    if args.title is not None:
        kw["title"] = args.title
    if args.point is not None:
        kw["summary"] = args.point
    if args.detail is not None:
        kw["detail"] = args.detail
    if args.surface_on is not None:
        kw["surface_on"] = args.surface_on
    if args.priority is not None:
        kw["priority"] = args.priority

    item = waypoints_core.edit_item(store["items"], args.id, **kw)
    if not item:
        print(f"Error: Waypoint '{args.id}' not found.")
        sys.exit(1)
    waypoints_core.save_store(store)
    print(f"Updated waypoint [{item['id']}]")


def cmd_show(args):
    store = waypoints_core.load_store()
    item = waypoints_core.get_item(store["items"], args.id)
    if not item:
        print(f"Error: Waypoint '{args.id}' not found.")
        sys.exit(1)
    status = "DONE" if item.get("done") else "OPEN"
    print(f"[{status}] {item.get('id')}: {item.get('title')}")
    if item.get("surface_on"):
        print(f"  Surface on: {item.get('surface_on')}")
    if item.get("created"):
        print(f"  Created: {item.get('created')}")
    if item.get("priority"):
        print(f"  Priority: {item.get('priority')}")
    if item.get("summary"):
        print("  Summary:")
        for s in item["summary"]:
            print(f"    - {s}")
    if item.get("detail"):
        print(f"  Detail:\n    {item['detail']}")


def cmd_done(args):
    store = waypoints_core.load_store()
    item = waypoints_core.mark_done(store["items"], args.id, outcome=args.outcome)
    if not item:
        print(f"Error: Waypoint '{args.id}' not found.")
        sys.exit(1)
    waypoints_core.save_store(store)
    print(f"Marked done [{item['id']}]: {item['title']}")


def cmd_reopen(args):
    store = waypoints_core.load_store()
    item = waypoints_core.get_item(store["items"], args.id)
    if not item:
        print(f"Error: Waypoint '{args.id}' not found.")
        sys.exit(1)
    item["done"] = False
    waypoints_core.save_store(store)
    print(f"Reopened waypoint [{item['id']}]")


def cmd_toggle(args):
    store = waypoints_core.load_store()
    item = waypoints_core.get_item(store["items"], args.id)
    if not item:
        print(f"Error: Waypoint '{args.id}' not found.")
        sys.exit(1)
    item["done"] = not item.get("done", False)
    waypoints_core.save_store(store)
    state = "DONE" if item["done"] else "OPEN"
    print(f"Toggled waypoint [{item['id']}] -> {state}")


def cmd_priority(args):
    store = waypoints_core.load_store()
    item = waypoints_core.edit_item(store["items"], args.id, priority=args.level)
    if not item:
        print(f"Error: Waypoint '{args.id}' not found.")
        sys.exit(1)
    waypoints_core.save_store(store)
    print(f"Set priority of [{item['id']}] to {args.level}")


def cmd_prune(args):
    store = waypoints_core.load_store()
    before = len(store["items"])
    store["items"] = [i for i in store["items"] if not i.get("done")]
    after = len(store["items"])
    waypoints_core.save_store(store)
    print(f"Pruned {before - after} done item(s). {after} item(s) remaining.")


def main():
    parser = argparse.ArgumentParser(description="Waypoints CLI for Google Antigravity")
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="List all open waypoints")

    # add
    p_add = subparsers.add_parser("add", help="Add a new waypoint")
    p_add.add_argument("title", help="Waypoint title")
    p_add.add_argument("--point", "-p", action="append", help="Summary bullet point")
    p_add.add_argument("--detail", "-d", help="Full detail string")
    p_add.add_argument("--surface-on", help="Earliest date to surface (YYYY-MM-DD)")
    p_add.add_argument("--priority", type=int, default=0, help="Priority level (higher sorts earlier)")

    # edit
    p_edit = subparsers.add_parser("edit", help="Edit an existing waypoint")
    p_edit.add_argument("id", help="Waypoint ID")
    p_edit.add_argument("--title", help="New title")
    p_edit.add_argument("--point", "-p", action="append", help="New summary bullet points")
    p_edit.add_argument("--detail", help="New detail string")
    p_edit.add_argument("--surface-on", help="New earliest surface date")
    p_edit.add_argument("--priority", type=int, help="New priority level")

    # show
    p_show = subparsers.add_parser("show", help="Show full details of a waypoint")
    p_show.add_argument("id", help="Waypoint ID")

    # done
    p_done = subparsers.add_parser("done", help="Mark a waypoint as done")
    p_done.add_argument("id", help="Waypoint ID")
    p_done.add_argument("--as", dest="outcome", help="Rewrite title to resolution outcome")

    # reopen
    p_reopen = subparsers.add_parser("reopen", help="Reopen a done waypoint")
    p_reopen.add_argument("id", help="Waypoint ID")

    # toggle
    p_toggle = subparsers.add_parser("toggle", help="Toggle done status")
    p_toggle.add_argument("id", help="Waypoint ID")

    # priority
    p_prio = subparsers.add_parser("priority", help="Set priority level")
    p_prio.add_argument("id", help="Waypoint ID")
    p_prio.add_argument("level", type=int, help="Priority level (integer)")

    # prune
    subparsers.add_parser("prune", help="Remove all done items from store")

    args = parser.parse_args()
    if not args.command:
        cmd_list(args)
        return

    funcs = {
        "list": cmd_list,
        "add": cmd_add,
        "edit": cmd_edit,
        "show": cmd_show,
        "done": cmd_done,
        "reopen": cmd_reopen,
        "toggle": cmd_toggle,
        "priority": cmd_priority,
        "prune": cmd_prune,
    }
    funcs[args.command](args)


if __name__ == "__main__":
    main()
