#!/usr/bin/env python3
"""CLI utility for Antigravity Local Model Delegation.

Commands:
  models    List supported model aliases and descriptions
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

    # check command
    check_p = subparsers.add_parser("check", help="Health-check local server")
    check_p.add_argument("--endpoint", default=None, help="Custom server URL")

    # dispatch command
    dispatch_p = subparsers.add_parser("dispatch", help="Dispatch prompt to local model")
    dispatch_p.add_argument("--model", default="qwen-3.6-operator", help="Model alias")
    dispatch_p.add_argument("--prompt", required=True, help="Task prompt string")
    dispatch_p.add_argument("--files", nargs="*", default=[], help="Optional file paths")
    dispatch_p.add_argument("--endpoint", default=None, help="Custom server URL")

    args = parser.parse_args()

    if args.command == "models":
        print("Available Local Model Aliases:\n")
        for alias, info in core.MODEL_CATALOG.items():
            print(f"- `{alias}`:")
            print(f"    Description: {info['description']}")
            print(f"    Model ID:    {info['default_model_id']}")
            print(f"    Context:     {info['context_window']} tokens\n")

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
