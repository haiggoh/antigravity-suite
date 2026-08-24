---
name: measure-twice
description: >-
  Pre-automation survey skill. Before building custom scripts or automation, survey for what
  already exists (OS utilities, shell builtins, platform APIs, existing project helpers) and
  match the trigger to the real event. Invoke when the user asks to automate something, create
  a new script, add a watcher/scheduler, or build a helper that might already exist.
---

# measure-twice — survey before you build

Before writing any automation, script, watcher, scheduled task, or helper utility:

## 1. Survey What Exists

- **OS/Shell builtins**: Check if `cron`, `launchd`, `Task Scheduler`, `systemd timers`, `fswatch`, `inotifywait`, or similar platform tools already handle the trigger.
- **Project utilities**: Search the codebase for existing helper scripts, Makefiles, npm scripts, or CI workflows that already do (or nearly do) what's requested.
- **Package ecosystem**: Check if a well-maintained package/tool already solves this (e.g., `watchman`, `entr`, `nodemon`, `chokidar`).

## 2. Match the Trigger to the Real Event

- Identify the **actual event** the automation should respond to (file change, git hook, schedule, HTTP webhook, user action).
- Verify the trigger fires in the real environment — don't assume based on documentation alone.
- If the trigger is a schedule, confirm the cadence with the user before implementing.

## 3. Build Only What's Missing

- If an existing tool covers 80%+ of the need, extend or wrap it rather than building from scratch.
- If building new, keep it minimal and composable (small scripts > monolithic solutions).
- Document why existing alternatives were rejected.
