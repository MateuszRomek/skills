from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("session-hook.py")
FOREIGN = {
    "theme": "auto",
    "hooks": {
        "SessionStart": [{"hooks": [{"type": "command", "command": "/opt/notify.sh"}]}],
        "Stop": [{"hooks": [{"type": "command", "command": "/opt/notify.sh"}]}],
    },
}


def run(root: Path, host: str, scope: str, state: str) -> None:
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CONFIG_DIR", "CODEX_HOME")}
    subprocess.run(
        [sys.executable, str(SCRIPT), host, scope, state, "--repo", str(root / "repo"), "--home", str(root / "home")],
        check=True,
        capture_output=True,
        env=env,
    )


class SessionHookTests(unittest.TestCase):
    def test_each_target_gets_one_entry_and_off_restores_the_file(self) -> None:
        cases = {
            ("claude-code", "repo"): ("repo/.claude/settings.json", '"$CLAUDE_PROJECT_DIR/.agents/agent-mode/session-start.md"'),
            ("claude-code", "global"): ("home/.claude/settings.json", "/home/.agents/agent-mode/session-start.md"),
            ("codex", "repo"): ("repo/.codex/hooks.json", "$(git rev-parse --show-toplevel)/.agents/agent-mode/session-start.md"),
            ("codex", "global"): ("home/.codex/hooks.json", "/home/.agents/agent-mode/session-start.md"),
        }
        for (host, scope), (relative, expected) in cases.items():
            with self.subTest(host=host, scope=scope), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / relative
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(FOREIGN))

                run(root, host, scope, "on")
                run(root, host, scope, "on")
                groups = json.loads(path.read_text())["hooks"]["SessionStart"]
                commands = [hook["command"] for group in groups for hook in group["hooks"]]
                self.assertEqual(commands[0], "/opt/notify.sh")
                self.assertEqual(len(commands), 2)
                self.assertIn(expected, commands[1])
                self.assertEqual(groups[1]["matcher"], "startup|resume|clear|compact")

                run(root, host, scope, "off")
                self.assertEqual(json.loads(path.read_text()), FOREIGN)

    def test_off_without_a_settings_file_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run(root, "codex", "global", "off")
            self.assertFalse((root / "home/.codex/hooks.json").exists())

    def test_installed_command_prints_the_routing_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            (repo / ".agents/agent-mode").mkdir(parents=True)
            (repo / ".agents/agent-mode/session-start.md").write_text("ROUTE\n")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / "sub").mkdir()

            run(root, "codex", "repo", "on")
            command = json.loads((repo / ".codex/hooks.json").read_text())["hooks"]["SessionStart"][0]["hooks"][0]["command"]
            result = subprocess.run(["sh", "-c", command], cwd=repo / "sub", capture_output=True, text=True)
            self.assertEqual(result.stdout, "ROUTE\n")

            (repo / ".agents/agent-mode/session-start.md").unlink()
            result = subprocess.run(["sh", "-c", command], cwd=repo / "sub", capture_output=True, text=True)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))


if __name__ == "__main__":
    unittest.main()
