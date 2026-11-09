#!/usr/bin/env python3

import argparse
import importlib.util
import os
from pathlib import Path

PREFIX = "am-"
OWNED = "Agent mode worker pinned to"
SCRIPTS = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("validate_profile", SCRIPTS / "validate-profile.py")
validate_profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_profile)


def pairs(profile_path: Path) -> list[tuple[str, str]]:
    profile = validate_profile.parse_profile(profile_path)
    found = {
        (worker["model"], worker["reasoning"])
        for route in profile.roles.values()
        for worker in route.workers
        if worker.get("model") and worker.get("reasoning") and worker["model"] != "inherit-parent"
    }
    return sorted(found)


def slug(value: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in value.lower()).strip("-")


def definition(model: str, reasoning: str) -> tuple[str, str]:
    name = f"{PREFIX}{slug(model)}-{slug(reasoning)}"
    return name, f"""---
name: {name}
description: {OWNED} {model} with {reasoning} effort. Use only when the selected Agent mode profile routes a role to model "{model}" with reasoning "{reasoning}"; the brief must state the role, scope, remaining budget, and evidence to return.
model: {model}
effort: {reasoning}
---

You are an Agent mode worker. Do only the bounded task in your brief, stay inside the scope and writable location it names, and return the evidence it asks for. Report consumed and unused delegation credits when the brief gives you any.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Write one Claude Code subagent per model and effort pair the profile routes to.")
    parser.add_argument("scope", choices=["repo", "global"])
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--home", type=Path, default=Path.home())
    args = parser.parse_args()

    if args.scope == "global":
        profile = args.home / ".agents/agent-mode/models.claude-code.yaml"
        target = Path(os.environ.get("CLAUDE_CONFIG_DIR", args.home / ".claude")) / "agents"
    else:
        profile = args.repo / ".agents/agent-mode/models.claude-code.yaml"
        target = args.repo / ".claude/agents"
    if not profile.is_file():
        raise SystemExit(f"blocked: no profile at {profile}")

    wanted = dict(definition(model, reasoning) for model, reasoning in pairs(profile))
    target.mkdir(parents=True, exist_ok=True)
    for stale in target.glob(f"{PREFIX}*.md"):
        if stale.stem not in wanted and OWNED in stale.read_text():
            stale.unlink()
            print(f"removed: {stale}")
    for name, text in wanted.items():
        path = target / f"{name}.md"
        if not path.is_file() or path.read_text() != text:
            path.write_text(text)
            print(f"wrote: {path}")
    print(f"agents: {', '.join(wanted) or 'none'}")


if __name__ == "__main__":
    main()
