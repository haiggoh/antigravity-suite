---
name: cost-tracker
description: "Use when reporting, reconciling, or reasoning about Antigravity / Gemini / Claude API spend — today's cost, a session's cost, whether a budget cap is close, what local offload saved, or why two spend figures disagree. Also use before writing any dollar figure about token spend into a message, a note, or a status line, and when the cost ledger looks wrong. ALSO use whenever the daily budget cap has changed or was raised/lowered (`cost-tracker cap --learn`)."
---

# cost-tracker

## The One Rule

**Every dollar figure names its own membership.** An unlabelled figure is not a minor style problem; it is the failure mode this tool was built to eliminate.

| Axis | Means | Never |
|---|---|---|
| `session` | one session's LIFETIME cost, possibly across several UTC days | called "today" |
| `today` | gateway spend across ALL sessions with an entry on one UTC day | assumed to exclude the current session |
| `local` | localhost inference — free compute, reported as savings | added to cloud spend |

Two dollar figures on one line with only one label is ambiguous. The status line shows a session-lifetime `$cost`, and the cost-tracker segment says `today: cloud …` out loud for exactly that reason.

## Commands

```bash
agy-cost-tracker report                      # today, per-session table
agy-cost-tracker report --week --json        # 7 days; --month, --since YYYY-MM-DD
agy-cost-tracker statusline                  # today: cloud $30.12/$40 · local saved $4.80
agy-cost-tracker doctor                      # quarantined records + resolved config
agy-cost-tracker calibrate                   # our daily totals vs the gateway's own figure
agy-cost-tracker cap --learn                 # learns cap from latest refusal turn
```

## Reading It Honestly

- **The cap is LEARNED or configured:** `agy-cost-tracker cap --learn` parses the newest gateway rejection message for budget limits. An explicit `AGY_BUDGET_CAP_USD` / `COST_TRACKER_CAP_USD` overrides it.
- **Local savings are distinct from $0 cloud spend:** Local offload savings are calculated via `agy-savings-ledger` and reported as `local saved: $X.XX`.
- **Today is UTC:** Aligns with cloud gateway quota windows.
