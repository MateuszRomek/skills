from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("program.py")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


class ProgramTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.program = str(Path(self.tmp.name) / "difi")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def init(self, *tasks: str) -> None:
        result = run("init", self.program, *tasks)
        self.assertEqual(result.returncode, 0, result.stderr)

    def move(self, task: str, status: str, *fields: str) -> subprocess.CompletedProcess[str]:
        return run("set", self.program, task, "--status", status, *fields)

    def test_ready_lists_only_tasks_whose_dependencies_merged(self) -> None:
        self.init("3|Auth", "5|Feed", "7|Profile|3")
        out = run("ready", self.program).stdout
        self.assertIn("start: 3", out)
        self.assertIn("start: 5", out)
        self.assertNotIn(": 7", out)
        for status in ("building", "verifying", "merging", "merged"):
            self.assertEqual(self.move("3", status).returncode, 0)
        self.assertIn("start: 7", run("ready", self.program).stdout)

    def test_limit_counts_building_tasks(self) -> None:
        self.init("1|A", "2|B", "3|C", "4|D")
        self.move("1", "building")
        out = run("ready", self.program, "--limit", "3").stdout
        self.assertIn("building: 1 of 3", out)
        self.assertIn("start: 2", out)
        self.assertIn("start: 3", out)
        self.assertIn("waiting-for-slot: 4", out)

    def test_dependent_task_cannot_start_before_its_dependency_merges(self) -> None:
        self.init("3|Auth", "7|Profile|3")
        result = self.move("7", "building")
        self.assertEqual(result.returncode, 1)
        self.assertIn("without a merge or a stack base: 3", result.stderr)

    def test_illegal_transition_is_rejected(self) -> None:
        self.init("1|A")
        result = self.move("1", "merged")
        self.assertEqual(result.returncode, 1)
        self.assertIn("queued -> merged is not allowed", result.stderr)

    def test_cycle_and_unknown_dependency_are_rejected(self) -> None:
        self.assertIn("cycle", run("init", self.program, "1|A|2", "2|B|1").stderr)
        self.assertIn("unknown task", run("init", self.program, "1|A|9").stderr)

    def test_init_is_idempotent(self) -> None:
        self.init("1|A")
        self.move("1", "building", "branch=orch/difi/1")
        again = run("init", self.program, "1|Different")
        self.assertIn("exists: 1 tasks", again.stdout)
        self.assertIn("1\tbuilding\tstandard", run("show", self.program).stdout)

    def test_retry_counts_attempts_and_fields_persist(self) -> None:
        self.init("1|A")
        self.move("1", "building")
        self.move("1", "queued", "note=context limit")
        self.assertIn("attempts 2", self.move("1", "building", "pr=https://example.test/pr/4").stdout)
        self.assertIn("https://example.test/pr/4", run("show", self.program).stdout)

    def test_show_reports_settled_when_every_task_is_merged_or_parked(self) -> None:
        self.init("1|A", "2|B")
        for status in ("building", "verifying", "merging", "merged"):
            self.move("1", status)
        self.assertIn("program: open", run("show", self.program).stdout)
        self.move("2", "parked", "note=needs product call")
        self.assertIn("program: settled", run("show", self.program).stdout)

    def advance(self, task: str, *statuses: str) -> None:
        for status in statuses:
            result = self.move(task, status)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_stack_on_a_dependency_that_has_a_pr(self) -> None:
        self.init("3|Auth", "7|Profile|3")
        self.advance("3", "building")
        self.assertNotIn("can-stack", run("ready", self.program).stdout)
        self.advance("3", "verifying")
        self.assertIn("can-stack: 7 on 3", run("ready", self.program).stdout)
        result = self.move("7", "building", "base=3")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("7\tbuilding\tstandard\tdeps[3]\ton[3]", run("show", self.program).stdout)

    def test_stacked_task_merges_only_after_its_base_and_then_needs_a_restack(self) -> None:
        self.init("3|Auth", "7|Profile|3")
        self.advance("3", "building", "verifying")
        self.move("7", "building", "base=3")
        self.advance("7", "verifying")
        blocked = self.move("7", "merging")
        self.assertEqual(blocked.returncode, 1)
        self.assertIn("cannot merge before its dependencies merge: 3", blocked.stderr)
        self.advance("3", "merging", "merged")
        self.assertIn("restack: 7 onto main, 3 merged", run("ready", self.program).stdout)
        self.assertEqual(run("set", self.program, "7", "base=main").returncode, 0)
        self.assertNotIn("restack", run("ready", self.program).stdout)
        self.advance("7", "merging", "merged")

    def test_base_must_be_main_or_a_dependency(self) -> None:
        self.init("1|A", "2|B")
        result = run("set", self.program, "2", "base=1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("base must be main or one of its dependencies", result.stderr)

    def test_stack_needs_every_other_dependency_merged(self) -> None:
        self.init("1|A", "2|B", "3|C|1,2")
        self.advance("1", "building", "verifying")
        self.assertNotIn("can-stack", run("ready", self.program).stdout)
        result = self.move("3", "building", "base=1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("without a merge or a stack base: 2", result.stderr)

    def test_level_defaults_to_standard_and_accepts_only_known_levels(self) -> None:
        self.init("1|A")
        self.assertEqual(run("set", self.program, "1", "level=behavioral").returncode, 0)
        self.assertIn("1\tqueued\tbehavioral", run("show", self.program).stdout)
        result = run("set", self.program, "1", "level=paranoid")
        self.assertEqual(result.returncode, 1)
        self.assertIn("level must be one of", result.stderr)

    def test_fix_rounds_stop_at_the_budget(self) -> None:
        self.init("1|A")
        self.advance("1", "building", "verifying", "building", "verifying")
        result = self.move("1", "building")
        self.assertEqual(result.returncode, 1)
        self.assertIn("spent its fix budget (1 of 1)", result.stderr)
        self.assertIn("fixes 1/1", run("show", self.program).stdout)
        self.advance("1", "parked")

    def test_raised_budget_allows_another_fix_round(self) -> None:
        self.init("1|A")
        self.advance("1", "building", "verifying", "building", "verifying")
        self.assertEqual(run("set", self.program, "1", "max_fixes=2").returncode, 0)
        self.advance("1", "building")
        self.assertIn("fixes 2/2", run("show", self.program).stdout)

    def test_rebase_from_merging_does_not_spend_the_fix_budget(self) -> None:
        self.init("1|A")
        self.advance("1", "building", "verifying", "merging", "building", "verifying", "building")
        self.assertIn("fixes 1/1", run("show", self.program).stdout)

    def test_a_program_written_before_the_fix_budget_loads_with_defaults(self) -> None:
        self.init("1|A")
        path = Path(self.program) / "tasks.tsv"
        old = ["id", "title", "deps", "base", "level", "status", "attempts", "branch", "pr", "head", "verdict", "updated", "note"]
        rows = [line.split("\t") for line in path.read_text().splitlines()]
        header = rows[0]
        path.write_text("".join("\t".join(r[header.index(c)] for c in old) + "\n" for r in rows))
        self.assertIn("fixes 0/1", run("show", self.program).stdout)
        self.advance("1", "building")
        self.assertIn("max_fixes", path.read_text().splitlines()[0])

    def test_unknown_field_is_rejected(self) -> None:
        self.init("1|A")
        result = run("set", self.program, "1", "status=merged")
        self.assertEqual(result.returncode, 1)
        self.assertIn("must be key=value", result.stderr)


if __name__ == "__main__":
    unittest.main()
