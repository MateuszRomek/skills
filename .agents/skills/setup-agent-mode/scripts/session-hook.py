#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path

MARKER = ".agents/agent-mode/session-start.md"
HOOKS_DIR = ".agents/agent-mode/hooks/"
MATCHER = "startup|resume|clear|compact"
CLAUDE_REMINDER = (
    ("UserPromptSubmit", None, "agent-mode-reminder.sh"),
    ("PostToolUse", "Skill", "agent-mode-mark.sh"),
)


def root_prefix(host: str, scope: str, home: Path) -> str:
    if scope == "global":
        return str(home)
    return "$CLAUDE_PROJECT_DIR" if host == "claude-code" else "$(git rev-parse --show-toplevel)"


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
    command = hook.get("command", "")
    return MARKER in command or HOOKS_DIR in command


def replace_owned(hooks: dict, event: str, entry: dict | None) -> None:
    groups = []
    for group in hooks.get(event, []):
        kept = [hook for hook in group.get("hooks", []) if not owned(hook)]
        if kept:
            groups.append({**group, "hooks": kept})
    if entry:
        groups.append(entry)
    if groups:
        hooks[event] = groups
    else:
        hooks.pop(event, None)


def entry(matcher: str | None, command: str, **extra) -> dict:
    group = {"matcher": matcher} if matcher else {}
    return {**group, "hooks": [{"type": "command", "command": command, **extra}]}


def apply(settings: dict, command: str, enabled: bool, reminder: list[tuple[str, str | None, str]] = ()) -> dict:
    hooks = settings.setdefault("hooks", {})
    replace_owned(hooks, "SessionStart", entry(MATCHER, f"{command} 2>/dev/null || true") if enabled else None)
    for event, matcher, script in reminder:
        replace_owned(hooks, event, entry(matcher, script, timeout=5) if enabled else None)
    if not hooks:
        settings.pop("hooks")
    return settings


def reminder_hooks(host: str, scope: str, home: Path) -> list[tuple[str, str | None, str]]:
    if host != "claude-code":
        return []
    prefix = root_prefix(host, scope, home)
    return [(event, matcher, f'"{prefix}/{HOOKS_DIR}{script}"') for event, matcher, script in CLAUDE_REMINDER]


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
    updated = apply(settings, command, args.state == "on", reminder_hooks(args.host, args.scope, args.home))
    if not updated and not path.is_file():
        print(f"{args.state}: {path} (unchanged)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(updated, indent=2) + "\n")
    print(f"{args.state}: {path}")


if __name__ == "__main__":
    main()
