---
name: waypoints
description: >-
  Use to manage the user's persistent open-items reminder ("waypoints") — the PreInvocation banner
  that lists unfinished tasks/follow-ups and stays until each is marked done. Invoke when adding a
  follow-up you want surfaced next session, marking one done, listing what's open, or reconciling the
  store during session wrap-up. Also invoke on generic open-item language ("add this to my to-do list",
  "track this as a loose end", "remind me about X next time", "don't let me forget this", "keep this on my radar").
---

# waypoints — persistent open-items reminder for Google Antigravity

A "waypoint" is a point still **ahead** of you on the journey — an unfinished task or follow-up you want surfaced at the start of every session **until you reach (complete) it**.

Unlike native checkpoints, waypoints are **forward-looking** and **persist until explicitly marked done**.

## The Store

`~/.gemini/waypoints.json` (overridable with `$WAYPOINTS_FILE`), structured as:

```json
{
  "version": 1,
  "items": [
    {
      "id": "kebab-slug",
      "title": "one-line headline (banner)",
      "summary": ["key point", "another"],
      "detail": "full continuity dump (on-demand only)",
      "surface_on": "YYYY-MM-DD or null",
      "created": "YYYY-MM-DD",
      "done": false,
      "priority": 0
    }
  ]
}
```

`surface_on` is the **earliest** date an item appears. Undated items show every session; dated ones show on and after that date, and both persist until marked `done`.

## Managing Waypoints

The user manages waypoints **by talking to you**. Use the CLI tool:

```sh
python3 ./bin/waypoints.py list
python3 ./bin/waypoints.py add "Title" [--point "key pt"...] [--detail "..."] [--surface-on YYYY-MM-DD] [--priority 0]
python3 ./bin/waypoints.py edit <id> [--title "..."] [--point "..."] [--detail "..."] [--surface-on YYYY-MM-DD]
python3 ./bin/waypoints.py show <id>     # print title + summary + full detail (the "pick it up" view)
python3 ./bin/waypoints.py done <id> [--as "outcome"]  # mark done; --as rewrites the title to resolution
python3 ./bin/waypoints.py reopen <id>   # undo a done state
python3 ./bin/waypoints.py toggle <id>   # flip done state
python3 ./bin/waypoints.py priority <id> <level>
python3 ./bin/waypoints.py prune        # drop all done items
```

## When to Act

- **When you see open waypoints in context**: Help progress the relevant item(s). When genuinely finished, mark done (`waypoints.py done <id>`).
- **When creating a follow-up**: Add it with `waypoints.py add "Title"`.
- **Session wrap-up**: Reconcile open items (`done` completed items, `add` newly created follow-ups).
