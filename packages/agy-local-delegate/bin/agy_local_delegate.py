#!/usr/bin/env python3
"""CLI utility for Antigravity Local Model Delegation.

Commands:
  models    List supported model aliases and descriptions
  scan      Scan local disk (~/.models) for installed models and report sizes
  check     Check if local inference server is running and reachable
  dispatch  Send prompt and optional files to local model
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_local_delegate_core as core


def main():
    parser = argparse.ArgumentParser(description="Antigravity Local Model Delegate CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # models command
    subparsers.add_parser("models", help="List available local model aliases")

    # scan command
    scan_p = subparsers.add_parser("scan", help="Scan local disk directory for installed models")
    scan_p.add_argument("--dir", default=None, help="Custom models directory to scan")

    # check command
    check_p = subparsers.add_parser("check", help="Health-check local server")
    check_p.add_argument("--endpoint", default=None, help="Custom server URL")

    # preflight command
    preflight_p = subparsers.add_parser("preflight", help="Run RAM preflight check before loading model")
    preflight_p.add_argument("--model", default="qwen-3.8-operator", help="Model alias to check (Default: qwen-3.8-operator)")
    preflight_p.add_argument("--floor", type=float, default=16.0, help="Floor RAM to preserve in GB (Default: 16)")
    preflight_p.add_argument("--overhead", type=float, default=6.0, help="Runtime overhead in GB (Default: 6)")
    preflight_p.add_argument("--dir", default=None, help="Custom models directory")

    # menu command (csl-style picker)
    subparsers.add_parser("menu", help="Interactive model selection picker (csl)")

    # dispatch command
    dispatch_p = subparsers.add_parser("dispatch", help="Dispatch prompt to local model")
    dispatch_p.add_argument("--model", default="qwen-3.8-operator", help="Model alias (Default: qwen-3.8-operator)")
    dispatch_p.add_argument("--prompt", required=True, help="Task prompt string")
    dispatch_p.add_argument("--files", nargs="*", default=[], help="Optional file paths")
    dispatch_p.add_argument("--endpoint", default=None, help="Custom server URL")

    args = parser.parse_args()

    if args.command == "models":
        print("Available Local Model Profiles:\n")
        for alias, info in core.MODEL_CATALOG.items():
            tag = " (Default)" if info.get("is_default") else ""
            print(f"- `{alias}`{tag}:")
            print(f"    Description: {info['description']}")
            print(f"    Subdir:      {info.get('subdir', 'N/A')}")
            print(f"    Model ID:    {info['default_model_id']}")
            print(f"    Context:     {info['context_window']} tokens\n")

    elif args.command == "scan":
        scan_res = core.scan_local_models_dir(args.dir)
        models_dir = scan_res["models_dir"]
        if not scan_res["exists"]:
            print(f"[-] Models directory not found at: {models_dir}")
            sys.exit(1)

        print(f"[*] Scanned Local Models Directory: {models_dir}\n")
        installed = scan_res["installed_catalog"]
        print(f"📦 Registered Catalog Models Installed ({len(installed)}):\n")
        for m in installed:
            print(f"  ✅ `{m['alias']}` ({m['size_gb']} GB): {m['description']}")
            print(f"     Subdirectory: {m['subdir']}")
        
        unreg = scan_res["unregistered_models"]
        if unreg:
            print(f"\n📂 Other Models / Artifacts on Disk ({len(unreg)}):\n")
            for u in unreg:
                print(f"  • {u['name']} ({u['size_gb']} GB)")

    elif args.command == "check":
        res = core.check_server_health(args.endpoint)
        if res.get("online"):
            print(f"[+] Local model server ONLINE at {res['endpoint']}")
            if res.get("available_models"):
                print(f"    Active models: {', '.join(res['available_models'])}")
            sys.exit(0)
        else:
            print(f"[-] Local model server OFFLINE at {res['endpoint']}")
            print(f"    Error: {res.get('error')}")
            sys.exit(1)

    elif args.command == "preflight":
        res = core.ram_preflight_check(
            model_alias=args.model,
            floor_gb=args.floor,
            overhead_gb=args.overhead,
            models_dir=args.dir,
        )
        if res.get("already_served"):
            print(f"✅ RAM Preflight: {res['message']}")
            sys.exit(0)
        elif res.get("fits"):
            print(f"✅ RAM Preflight: {res['model_alias']} is SAFE to load.")
            print(f"   {res['message']}")
            print(f"   Available: {res['available_gb']} GB | Total: {res['total_gb']} GB | Kept floor: {res['floor_gb']} GB")
            sys.exit(0)
        else:
            print(f"⚠️  RAM Preflight: Loading {res['model_alias']} looks UNSAFE right now!", file=sys.stderr)
            print(f"   {res['message']}", file=sys.stderr)
            print(f"   Available: {res['available_gb']} GB | Needs: ~{res['need_gb']} GB (weights {res['weights_gb']} + {res['overhead_gb']} GB overhead)", file=sys.stderr)
            sys.exit(1)

    elif args.command == "menu":
        scan = core.scan_local_models_dir()
        installed_subdirs = {m["subdir"]: m["size_gb"] for m in scan.get("installed_catalog", [])}
        active_servers = core.find_active_model_servers()
        running_models = {}
        for s in active_servers:
            for m in s.get("models", []):
                running_models[m] = s["port"]

        print("\n╔══════════════════════════════════════════════════════════════════════════╗", file=sys.stderr)
        print("║  🖥️  Antigravity Local Mode — Model Selection (csl)                      ║", file=sys.stderr)
        print("╚══════════════════════════════════════════════════════════════════════════╝\n", file=sys.stderr)

        items = []
        idx = 1
        for alias, info in core.MODEL_CATALOG.items():
            subdir = info.get("subdir", "")
            is_installed = subdir in installed_subdirs
            is_running = (
                info["default_model_id"] in running_models or
                alias in running_models or
                subdir in running_models
            )
            running_port = (
                running_models.get(info["default_model_id"]) or
                running_models.get(alias) or
                running_models.get(subdir)
            )

            status_tags = []
            if is_running:
                status_tags.append(f"[Active Port {running_port} 🔌]")
            if is_installed:
                size_gb = installed_subdirs[subdir]
                status_tags.append(f"[Installed {size_gb} GB ✅]")

            tag_str = " " + " ".join(status_tags) if status_tags else ""
            default_tag = " (Default)" if info.get("is_default") else ""

            print(f"  {idx}) {alias:<22}{default_tag}{tag_str}", file=sys.stderr)
            print(f"     └─ {info['description']}", file=sys.stderr)
            items.append((alias, info["default_model_id"]))
            idx += 1

        print("\n  c) Custom Model ID or path", file=sys.stderr)
        print("  q) Quit\n", file=sys.stderr)

        try:
            choice = input("Selection [1]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("", file=sys.stderr)
            sys.exit(1)

        if not choice:
            choice = "1"

        if choice.lower() == "q":
            sys.exit(1)
        elif choice.lower() == "c":
            try:
                custom_model = input("Enter custom model ID / path: ").strip()
                if not custom_model:
                    sys.exit(1)
                print(custom_model)
                sys.exit(0)
            except (EOFError, KeyboardInterrupt):
                sys.exit(1)
        elif choice.isdigit() and 1 <= int(choice) <= len(items):
            selected_alias, selected_id = items[int(choice) - 1]
            print(selected_alias)
            sys.exit(0)
        else:
            print(f"Invalid selection: {choice}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "dispatch":
        res = core.dispatch_local_prompt(
            prompt=args.prompt,
            model_alias=args.model,
            files=args.files,
            endpoint=args.endpoint,
        )
        if res.get("success"):
            print(res["reply"])
            sys.exit(0)
        else:
            print(f"[-] Delegation failed: {res.get('error')}", file=sys.stderr)
            if res.get("hint"):
                print(f"    Hint: {res.get('hint')}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
