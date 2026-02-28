#!/usr/bin/env python3
"""Update Windsurf global MCP config from repository-local mcp.json."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def validate_repo_servers(raw: Dict[str, Any], source: Path) -> Dict[str, Dict[str, Any]]:
    servers = raw.get("mcpServers")
    if not isinstance(servers, dict):
        raise ValueError(f"{source} must contain a top-level object 'mcpServers'.")

    valid: Dict[str, Dict[str, Any]] = {}
    skipped = []

    for name, cfg in servers.items():
        if not isinstance(cfg, dict):
            skipped.append(name)
            continue
        if "command" not in cfg:
            skipped.append(name)
            continue
        valid[name] = cfg

    if skipped:
        print(
            "Skipped entries without runnable MCP config (missing object/command): "
            + ", ".join(sorted(skipped)),
            file=sys.stderr,
        )
    return valid


def ensure_global_shape(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {"mcpServers": {}}
    servers = raw.get("mcpServers")
    if not isinstance(servers, dict):
        raw["mcpServers"] = {}
    return raw


def parse_args() -> argparse.Namespace:
    default_source = Path(__file__).resolve().parents[1] / "mcp.json"
    default_target = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"

    parser = argparse.ArgumentParser(
        description="Merge repository MCP servers into Windsurf global mcp_config.json."
    )
    parser.add_argument("--source", type=Path, default=default_source, help="Repository MCP source file (default: ./mcp.json).")
    parser.add_argument("--target", type=Path, default=default_target, help="Windsurf global MCP config path.")
    parser.add_argument(
        "--mode",
        choices=("merge", "replace-managed"),
        default="merge",
        help="merge: upsert servers from source; replace-managed: clear previously managed servers then upsert.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show planned changes without writing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    target = args.target.expanduser().resolve()
    managed_key = "_managedByThisIsTheWay"

    if not source.exists():
        print(f"Source file not found: {source}", file=sys.stderr)
        print("Create/update mcp.json in your repository first.", file=sys.stderr)
        return 1

    try:
        repo_raw = load_json(source)
        repo_servers = validate_repo_servers(repo_raw, source)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not repo_servers:
        print("No runnable MCP servers found in source. Nothing to apply.", file=sys.stderr)
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        try:
            global_raw = ensure_global_shape(load_json(target))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    else:
        global_raw = {"mcpServers": {}}

    global_servers = global_raw["mcpServers"]
    changed = []

    if args.mode == "replace-managed":
        managed_names = [name for name, cfg in global_servers.items() if isinstance(cfg, dict) and cfg.get(managed_key) is True]
        for name in managed_names:
            del global_servers[name]
            changed.append(f"removed:{name}")

    for name, cfg in repo_servers.items():
        next_cfg = dict(cfg)
        next_cfg[managed_key] = True
        before = global_servers.get(name)
        if before != next_cfg:
            global_servers[name] = next_cfg
            changed.append(f"upserted:{name}")

    if not changed:
        print("No changes required. Windsurf MCP config is already up to date.")
        return 0

    print("Planned changes:")
    for item in changed:
        print(f"- {item}")

    if args.dry_run:
        print("Dry run only. No files were changed.")
        return 0

    if target.exists():
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup = target.with_suffix(target.suffix + f".bak.{ts}")
        shutil.copy2(target, backup)
        print(f"Backup created: {backup}")

    target.write_text(json.dumps(global_raw, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Updated Windsurf MCP config: {target}")
    print("Next step: open Windsurf MCP settings and click Refresh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
