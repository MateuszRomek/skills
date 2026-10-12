#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
VALIDATE = SCRIPTS / "validate-profile.py"

SCOPES = (
    ("repo", "repo", "models.{host}.yaml"),
    ("global", "global", "models.{host}.yaml"),
)


def select(host: str, repo: Path, home: Path) -> tuple[str, Path] | None:
    roots = {
        "repo": repo / ".agents/agent-mode",
        "global": home / ".agents/agent-mode",
    }
    for scope, root_key, pattern in SCOPES:
        path = roots[root_key] / pattern.format(host=host)
        if path.is_file():
            return scope, path
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Select and validate the Agent mode profile.")
    parser.add_argument("host")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--home", type=Path, default=Path.home())
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z][a-z0-9-]*", args.host):
        raise SystemExit(f"invalid host slug: {args.host}")

    selected = select(args.host, args.repo, args.home)
    if selected is None:
        print("none")
        return

    scope, path = selected
    routing = path.parent / "ROUTING.md"
    if not routing.is_file():
        raise SystemExit(f"blocked: {scope} profile {path} has no ROUTING.md beside it")
    result = subprocess.run(
        [sys.executable, str(VALIDATE), str(path), str(routing)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        hint = ""
        if re.search(r"missing roles|unknown roles", detail):
            hint = (
                f"\nThe shared references in {path.parent} may be out of date. "
                "Rerun setup-agent-mode to refresh them."
            )
        raise SystemExit(f"blocked: {scope} profile {path}: {detail}{hint}")
    host_line = re.search(r"^host:\s*['\"]?([a-z][a-z0-9-]*)", path.read_text(), re.M)
    if not host_line or host_line.group(1) != args.host:
        raise SystemExit(f"blocked: {scope} profile {path} host does not match {args.host}")
    print(f"{scope}\t{path}")


if __name__ == "__main__":
    main()
