# Antigravity Tooling & Plugin Workspace (`D:\antigravity`)

Welcome to the **Antigravity Tooling & Plugin Workspace**. This workspace contains dedicated Antigravity plugins, rules, skills, and utilities maintained by [@haiggoh](https://github.com/haiggoh).

---

## Workspace Structure

```text
D:\antigravity\
├── GEMINI.md                    # Root workspace guidelines & coding rules
├── .agents/                     # Workspace-level agent customizations
│   ├── rules/                   # Workspace rules
│   └── skills/                  # Workspace skills
└── projects/                    # New, dedicated Antigravity plugin repositories (agy-*)
    ├── agy-no-hidden-changes/   # Antigravity rule plugin
    ├── agy-measure-twice/       # Antigravity skill plugin
    ├── agy-waypoints/           # Antigravity lifecycle hook & banner plugin
    ├── agy-audit-loose-ends/    # Antigravity stop hook & reconciliation plugin
    ├── agy-resume-interrupted/  # Antigravity session resumption hook plugin
    ├── agy-session-bundle/      # Antigravity transcript bundler utility
    ├── agy-desktop-sync/        # Antigravity MCP config sync utility
    ├── agy-blender-automation/  # Antigravity 3D modeling workflow skill
    └── get-haiggoh-agy/         # Antigravity package & plugin manager CLI
```

---

## Workspace Strategy & Rules

1. **Independent Repositories**: All Antigravity projects are brand-new, standalone repositories prefixed with `agy-`. Published Claude Code repositories remain completely untouched.
2. **Rule Enforcement**: Prefer visible, reversible, and honest code changes. Never use hidden workarounds (`agy-no-hidden-changes`).
3. **Measure Twice**: Survey existing capabilities and match real events before writing custom automation scripts (`agy-measure-twice`).
4. **Modular Design**: Keep individual plugins focused. Use progressive disclosure for skills and lifecycle hooks (`hooks.json`) for automatic interventions.
5. **Antigravity Standard Layout**: Every plugin contains a valid `plugin.json` manifest, along with optional `hooks.json`, `rules/`, and `skills/`.
