# Verification

Each PR is verified in **lanes**. A lane is one independent check run by a fresh worker that never wrote the code. A verdict covers one head SHA, and it is clean only when every lane the task's level requires returns `PASS` at that same SHA.

## Inventory the verification tools

At program start, look in `.agents/skills/` (and `.claude/skills/` when the repository keeps that layer) for project-local verification skills, and record each one in `program.md` under `Verification tools`:

- **App verify skill.** A skill with Launch, Doctor, Drive, Evidence, and Cleanup sections and a `features/` map, as `create-verification-skill` generates. Record its name, the surface it drives, and its feature files.
- **Formal check.** A skill that runs a model checker, prover, or code-level verifier against named code, as `create-formal-verification-skill` generates. Record its name, the property, the files it covers, and its run command.

A gap is a finding, not a blocker. A program with UI tasks and no app verify skill, or with tasks that change a state machine, retry logic, or concurrency that no formal check covers, gets a `findings.md` entry proposing `/create-verification-skill` or `/create-formal-verification-skill`, optionally as a task 0 when the user agrees.

## Levels

Assign each task a level when you build the graph with `program.py set <program-dir> <task> level=<level>`, and show the levels with the graph. Rules the user states in `program.md`, such as "everything in apps/web is behavioral", override these defaults.

| Level | Use for | Lanes |
| --- | --- | --- |
| `light` | docs, configuration, mechanical refactors with no behavior change | gates |
| `standard` | logic with no user-visible surface | gates, audit |
| `behavioral` | UI, CLI output, API responses, any change a user can observe | gates, live, audit |
| `security` | the security-sensitive areas listed in [`slicing.md`](slicing.md) | the `behavioral` or `standard` lanes with the security axis in audit, plus the **interrogate** skill on `interrogate-reviewers` |

## Lanes

| Lane | Role | Proves |
| --- | --- | --- |
| gates | `verify-gates` | The repository's checks for the touched paths pass at the head SHA, and every formal check whose covered files the diff touches passes. |
| live | `verify-live` | The done predicate holds on the running app, through the app verify skill when one exists. |
| audit | `verify-audit` | The diff meets its source and the repository's standards, has no correctness defect, and for a `security` task no security defect. It also judges every formal-check failure the gates lane reports. |

Start a task's lanes in parallel. Each lane counts against the worker limit.

**One review layer.** The audit lane is the program's code review. It covers these axes:

| Axis | How | When |
| --- | --- | --- |
| spec | the **spec-standards-review** skill, Spec axis | every audit |
| standards | the **spec-standards-review** skill, Standards axis | every audit |
| correctness | the lane's own read of the diff | every audit |
| security | the lane's own security read, beside **interrogate** | `security` tasks only |

`spec-standards-review` runs its two axes as two `verify-audit` units, so reserve two credits for each audit lane. When the user names further review skills, such as `code-review` or `security-review`, record them in `program.md` as audit-lane tools. The audit lane runs them, and only when the host has them. Review never becomes extra lanes, and workers never run review skills. The **thermo-nuclear-code-quality-review** skill never runs per task. It runs once at program close, per the orchestrate skill's step 6.

**Triage before fixing.** Read every lane's `Blocking` list yourself. A finding stays blocking only when it meets **What blocks** below. Move every other finding to `findings.md`. A round left with no blocking finding is a pass.

**Fix rounds.** A fix worker gets only the blocking findings. Each task has a fix budget, `max_fixes` in `program.py`, default 1. `program.py` refuses a fix round past it. A rule in `program.md` may raise it per task. After a fix, verify the fix, not the PR:

- rerun gates at the new head;
- run the **confirm** brief on `verify-audit`, which checks each fixed finding and nothing else;
- rerun live only when a fix touches behavior the done predicate covers, and only for the fixed scenarios.

A fix round never starts a fresh review of the delta. When confirm fails and the budget is spent, park the task and raise it with the findings at the next user message.

**Rebase and restack.** Rerun gates at the new head. Rerun audit on the delta only when `git patch-id` shows the code changed. Rerun live only when that change touches behavior the done predicate covers. A lane whose input is unchanged keeps its verdict.

**Regression risk.** A rebase or restack can break the task even when its own diff is unchanged. Treat it as a regression risk when the rebase resolved a conflict, or when what landed on main changed code the task calls, code that calls it, or state it shares. Then rerun the lanes that prove the done predicate on the new head, even with an unchanged `git patch-id`. That is live for a `behavioral` or `security` task, and gates otherwise. Drive only the done-predicate scenarios the risk reaches.

**What blocks.** Only what a lane can show: a failing run at the head, a requirement the diff misses or implements wrongly (spec `missing` or `wrong`), a breach of a documented repository standard (standards `hard`), a bug a user would hit, a security hole with a concrete path, a formal check failing on the current code, or a doc the PR made wrong. Spec `extra` and standards `judgement` findings are follow-ups. A problem the base already has blocks only when the PR copies it or newly reaches it. Everything else is a follow-up for `findings.md`.

## Lane briefs

Every lane brief opens with this header, filled in full:

```text
Goal of the program: <the user's goal, restated>
Task: <task id> <title>, level <level>
Source: <issue URL or spec section, with its full text pasted below>
Done predicate: <from program.md>
PR: <url>
Head SHA: <full SHA>
Scope: <full PR | delta from <old SHA> to <new SHA> | fixes listed below>
Delegation: reserved credits <n or unlimited>. Delegate through the agent-mode skill when your work calls for it.
You are read-only toward the PR. Never push, comment, approve, or merge.
Check out the head SHA in a scratch worktree of your own and remove it when done.
First confirm the PR head equals the head SHA. If it moved, stop and report STALE.
```

Then the lane's steps.

**gates**

```text
1. Run the repository's checks for the touched paths: tests, lint, type check, build.
2. For each formal check in this list whose covered files the diff touches, run its command as its skill says: <formal checks from program.md, or none>.
3. Report each command, its exit code, and the failing output verbatim. Do not interpret a formal-check failure. Report its counterexample as the tool printed it.
```

**live**

```text
1. Use the app verify skill <name, or none> to launch, run its doctor, and drive the app. Without one, use the host's browser, PTY, or simulator tools.
2. Prove the done predicate on the running app. Drive every entry point the feature map lists for the features this diff touches, not only the most convenient one. In a fix round, drive only the fixed scenarios.
3. Save one screenshot or transcript per scenario, showing the action's resulting state, to <program dir>/screenshots/<task id>/verify/ and compare them with the worker's screenshots in <program dir>/screenshots/<task id>/.
4. Check that the feature map files for the touched features still describe the app. A stale map entry is a finding.
5. Run the verify skill's cleanup. Confirm the evidence still exists afterwards.
```

**audit**

```text
1. Run the spec-standards-review skill with the PR's base as the fixed point and the source above as the spec. Keep each finding's axis and kind.
2. Audit for correctness: error paths, edge cases, concurrency, data shape changes and their callers.
3. For a security task only, audit for security: input validation at boundaries, authorization on every new path, secrets, injection, personal data exposure, unsafe defaults.
4. For each formal-check failure reported by the gates lane: <failures, or none>. Replay the counterexample against the real code, using the statechart skill for TLA+ results. Report it as a code bug when every step can happen in the code, or as model drift when one cannot.
5. Run each audit-lane tool from program.md: <code-review, security-review, or none>. Report its findings through the same blocking rule.
```

**confirm**

```text
Fixed findings: <each blocking finding from the last round, with file:line and how it reproduced>
1. For each finding, check that the diff since <old SHA> fixes it and that a test covers it, failing on <old SHA> and passing on the head when the finding was testable.
2. Review nothing else. A new problem you happen to see goes under Follow-ups, unless it is a regression the fix itself introduced.
```

Every lane reports in this shape:

```text
Lane: gates | live | audit | confirm
Verdict: PASS | ISSUES | STALE
Head: <the SHA you verified>
Evidence: <commands and results, screenshot paths>
Blocking: <one line per proven defect, with file:line and how to reproduce>
Follow-ups: <one line per non-blocking finding>
```
