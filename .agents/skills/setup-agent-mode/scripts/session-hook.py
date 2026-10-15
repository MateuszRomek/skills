#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path

MARKER = ".agents/agent-mode/session-start.md"
MATCHER = "startup|resume|clear|compact"


def targets(repo: Path, home: Path) -> dict[tuple[str, str], tuple[Path, str]]:
    claude_config = Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude"))
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
    return {
        ("claude-code", "repo"): (
            repo / ".claude/settings.json",
            f'cat "$CLAUDE_PROJECT_DIR/{MARKER}"',
        ),
        ("claude-code", "global"): (
            claude_config / "settings.json",
            f'cat "{home / MARKER}"',
        ),
        ("codex", "repo"): (
            repo / ".codex/hooks.json",
            f'cat "$(git rev-parse --show-toplevel)/{MARKER}"',
        ),
        ("codex", "global"): (
            codex_home / "hooks.json",
            f'cat "{home / MARKER}"',
        ),
    }


def owned(hook: dict) -> bool:
    return MARKER in hook.get("command", "")


def apply(settings: dict, command: str, enabled: bool) -> dict:
    hooks = settings.setdefault("hooks", {})
    groups = []
    for group in hooks.get("SessionStart", []):
        kept = [hook for hook in group.get("hooks", []) if not owned(hook)]
        if kept:
            groups.append({**group, "hooks": kept})
    if enabled:
        groups.append(
            {
                "matcher": MATCHER,
                "hooks": [{"type": "command", "command": f"{command} 2>/dev/null || true"}],
            }
        )
    if groups:
        hooks["SessionStart"] = groups
    else:
        hooks.pop("SessionStart", None)
    if not hooks:
        settings.pop("hooks")
    return settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn the Agent mode SessionStart hook on or off.")
    parser.add_argument("host", choices=["claude-code", "codex"])
    parser.add_argument("scope", choices=["repo", "global"])
    parser.add_argument("state", choices=["on", "off"])
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--home", type=Path, default=Path.home())
    args = parser.parse_args()

    path, command = targets(args.repo, args.home)[(args.host, args.scope)]
    settings = json.loads(path.read_text()) if path.is_file() else {}
    updated = apply(settings, command, args.state == "on")
    if not updated and not path.is_file():
        print(f"{args.state}: {path} (unchanged)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(updated, indent=2) + "\n")
    print(f"{args.state}: {path}")


if __name__ == "__main__":
    main()
