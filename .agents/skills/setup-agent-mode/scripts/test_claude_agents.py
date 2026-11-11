from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("claude-agents.py")
PROFILE = """version: 2
host: claude-code
intent:
  optimization: balanced
  budget: none
delegation:
  mode: enabled
  max-workers-per-task: unlimited
  max-concurrent-workers: 3
roles:
  feature:
    execution: workers
    workers:
      - model: opus
        reasoning: low
  review:
    execution: workers
    workers:
      - model: opus
        reasoning: low
      - model: haiku
        reasoning: medium
"""


def run(root: Path, scope: str) -> str:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
    return subprocess.run(
        [sys.executable, str(SCRIPT), scope, "--repo", str(root / "repo"), "--home", str(root / "home")],
        check=True, capture_output=True, text=True, env=env,
    ).stdout


class ClaudeAgentsTests(unittest.TestCase):
    def test_one_agent_per_pair_stale_owned_agents_removed_foreign_kept(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "home/.agents/agent-mode").mkdir(parents=True)
            (root / "home/.agents/agent-mode/models.claude-code.yaml").write_text(PROFILE)
            agents = root / "home/.claude/agents"
            agents.mkdir(parents=True)
            (agents / "am-sonnet-high.md").write_text("description: Agent mode worker pinned to sonnet\n")
            (agents / "am-custom.md").write_text("my own agent\n")

            run(root, "global")
            self.assertEqual(sorted(p.name for p in agents.iterdir()), ["am-custom.md", "am-haiku-medium.md", "am-opus-low.md"])
            text = (agents / "am-opus-low.md").read_text()
            self.assertIn("model: opus\n", text)
            self.assertIn("effort: low\n", text)
            self.assertEqual(run(root, "global").splitlines(), ["agents: am-haiku-medium, am-opus-low"])

    def test_missing_profile_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(subprocess.CalledProcessError):
                run(Path(directory), "repo")


if __name__ == "__main__":
    unittest.main()
