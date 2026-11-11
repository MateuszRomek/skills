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
| `security` | the security-sensitive areas listed in [`slicing.md`](slicing.md) | the `behavioral` or `standard` lanes, plus the **interrogate** skill on `interrogate-reviewers` |

## Lanes

| Lane | Role | Proves |
| --- | --- | --- |
| gates | `verify-gates` | The repository's checks for the touched paths pass at the head SHA, and every formal check whose covered files the diff touches passes. |
| live | `verify-live` | The done predicate holds on the running app, through the app verify skill when one exists. |
| audit | `verify-audit` | The diff meets its source, nothing beyond it, and has no correctness or security defect. It also judges every formal-check failure the gates lane reports. |

Start a task's lanes in parallel. Each lane counts against the worker limit.

**Fix rounds.** After a rebase, a restack, or a fix, rerun gates on the new head. Rerun audit when the code diff changed, which `git patch-id` shows. Rerun live when the change touches behavior the done predicate covers. A lane whose input is unchanged keeps its verdict.

**What blocks.** Only what a lane can show: a failing run at the head, a requirement the diff misses, a bug a user would hit, a security hole with a concrete path, a formal check failing on the current code, or a doc the PR made wrong. A problem the base already has blocks only when the PR copies it or newly reaches it. Everything else is a follow-up for `findings.md`.

## Lane briefs

Every lane brief opens with this header, filled in full:

```text
Goal of the program: <the user's goal, restated>
Task: <task id> <title>, level <level>
Source: <issue URL or spec section, with its full text pasted below>
Done predicate: <from program.md>
PR: <url>
Head SHA: <full SHA>
Scope: <full PR | delta from <old SHA> to <new SHA>>
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
2. Prove the done predicate on the running app. Drive every entry point the feature map lists for the features this diff touches, not only the most convenient one.
3. Save screenshots or transcripts of each action and its resulting state to <program dir>/screenshots/<task id>/verify/ and compare them with the worker's screenshots in <program dir>/screenshots/<task id>/.
4. Check that the feature map files for the touched features still describe the app. A stale map entry is a finding.
5. Run the verify skill's cleanup. Confirm the evidence still exists afterwards.
```

**audit**

```text
1. Audit the diff against the source: every requirement met, nothing beyond it.
2. Audit for correctness: error paths, edge cases, concurrency, data shape changes and their callers.
3. Audit for security: input validation at boundaries, authorization on every new path, secrets, injection, personal data exposure, unsafe defaults.
4. For each formal-check failure reported by the gates lane: <failures, or none>. Replay the counterexample against the real code, using the statechart skill for TLA+ results. Report it as a code bug when every step can happen in the code, or as model drift when one cannot.
```

Every lane reports in this shape:

```text
Lane: gates | live | audit
Verdict: PASS | ISSUES | STALE
Head: <the SHA you verified>
Evidence: <commands and results, screenshot paths>
Blocking: <one line per proven defect, with file:line and how to reproduce>
Follow-ups: <one line per non-blocking finding>
```
