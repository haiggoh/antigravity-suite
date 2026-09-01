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
