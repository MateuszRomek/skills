---
name: orchestrate
description: "Coordinate issues, a specification, or a multi-PR plan to merged pull requests from one chat: dispatch Agent mode workers in worktrees, verify each PR in independent lanes, merge or stack in dependency order, keep the program's memory in files, and report through ketchup. Use for /orchestrate, 'orchestrate', 'deliver these issues', 'take #3 to #12 to main', or resuming or checking on a running program."
---

# Orchestrate

**You run the program, never the code.** The user talks only to you. You split the work, start workers, check what each one produces, merge, and remember. Workers write the code. Adapted from the pstack Orchestrate and Autopilot-full playbooks for a single local coordinator on a bounded usage plan.

This skill is part of the Agent mode workflow. When the host refuses a skill it names because that skill is user-invoked only, such as **ketchup**, read its `SKILL.md` and follow it, per the Skills section of [`HOST-COMPATIBILITY.md`](../../agent-mode/HOST-COMPATIBILITY.md).

A program is one goal and its tasks. Its memory is the **program directory**, `.orchestrate/<slug>/` at the repository root. Your context window compacts and the chat may end, so anything you would need to remember goes into the program directory before you act on it.

```text
.orchestrate/<slug>/
  program.md      goal, task sources, done predicates, merge policy, the user's rules, gates
  tasks.tsv       one row per task, owned by scripts/program.py
  decisions.tsv   the show-me-your-work trail, one row per decision
  findings.md     problems found on the way and candidate new issues
  screenshots/<task-id>/
  worktrees/<task-id>/
```

You are the single writer of `program.md`, `tasks.tsv`, `decisions.tsv`, and `findings.md`. Workers return facts in their reports and write only their own branch and their own `screenshots/<task-id>/` folder (the **separate-before-serializing-shared-state** principle). Change `tasks.tsv` only through `python3 <skill dir>/scripts/program.py` (written `program.py` below), whose transitions are the task state machine:

```text
queued -> building -> verifying -> merging -> merged
building, verifying, merging -> back to an earlier state for a fix round
any open state -> parked -> queued once the user unblocks it
```

`building` refuses a task whose dependencies have not merged, except the one it stacks on. `merging` refuses a task until every dependency has merged, so stacks merge bottom-up.

## Authority

Invoking this skill with a delivery goal ("merged on main") is the user's explicit request for every PR and merge inside the program's task list. `program.md` records the merge policy the user chose: `merge` (default) or `stop-at-verified`, where you hand over verified green PRs and the user merges. The request covers nothing outside the task list.

Stop and ask only at a **gate**: a schema migration, a public contract change, authentication or permissions, a product call the specification does not settle, an irreversible action, a task parked after two failed attempts, or a task parked with its fix budget spent. `program.md` lists any extra gates the user named. Rebases, retries, flaky CI, review fixes, and "should I continue" are yours to settle (the **never-block-on-the-human** principle).

## 1. Open or resume the program

Restate the user's goal in your own words.

- **Resume** when `.orchestrate/<slug>/` exists. Read `program.md`, run `program.py show`, read the last rows of `decisions.tsv`. Reconcile every open task with live state: `gh pr view` and `gh pr checks` for its PR, `git branch -r` for its branch. Live state wins over the file. Record each correction as a decision row. Then continue at step 4.
- **Create** otherwise. Add `.orchestrate/` to `.git/info/exclude` when it is missing there. Write `program.md` from the request: the goal, the main SHA the program starts from, each task's source (issue number or spec section), each task's done predicate taken from its acceptance criteria, the merge policy, the user's rules (skills to use, screenshots, areas to avoid, verification rules, review skills the audit lane runs), and extra gates. Inventory the repository's verification skills per [`references/verification.md`](references/verification.md). Start `decisions.tsv` from the header in the **show-me-your-work** skill's `references/decision-log-template.tsv`.

The step is complete when the program directory exists and every open task's row matches its live PR and branch.

## 2. Build the task graph

The input is a list of issues, a specification, or a multi-phase plan. For a specification or a plan, cut the tasks per [`references/slicing.md`](references/slicing.md) first. For issues, read each one through the tracker that `docs/agents/issue-tracker.md` names, such as GitHub, GitLab, or Linear through its connector. Without that file, use `gh issue view` when the remote is GitHub, and otherwise ask the user where the issues live. Take dependencies from explicit links ("blocked by #3", "depends on", a spec's ordering). Infer a dependency only from a concrete shared surface, such as a migration another task reads or an API another task calls, and mark it `inferred` in `program.md`.

Create the rows with `program.py init <program-dir> 'id|title|dep,dep' ...`. It rejects unknown dependencies and cycles. Give each task a verification level per [`references/verification.md`](references/verification.md).

Show the user the graph, the start order, each task's level, and the verification gaps, and wait for their go. A task without a checkable done predicate is not ready. Ask for its predicate in the same message.

## 3. Arm delegation

Emit the Agent mode preflight per [`HOST-COMPATIBILITY.md`](../../agent-mode/HOST-COMPATIBILITY.md). Workers implement as the `feature` role, or `bug-fix` for a defect issue. Verification lanes run as `verify-gates`, `verify-live`, and `verify-audit`. Security tasks add the **interrogate** skill on `interrogate-reviewers`. The worker limit is the profile's concurrency limit, `delegation.max-concurrent-workers`: the most subagents that may run at the same time in this task, lanes and nested children included. The user's explicit number for this program overrides it. Record the limit in `program.md`. Pass each worker the credits you reserve for it per the delegation rules in that file, and count its children against the same limit. When the profile authorizes no workers, report it and stop.

## 4. Run the loop

Each wake (a worker report, a lane verdict, a user message) runs the same reconcile. Read the state, act on the difference, record it. The loop is idempotent, so a repeated wake finds nothing left to do (the **make-operations-idempotent** principle).

**Start with one task.** Take the first ready task all the way to merged before you fill the other slots. A flaw in the brief then costs one worker.

**Fill slots.** Run `program.py ready <program-dir> --limit <limit>`. For each `start:` line, move the task to `building` and create its worktree yourself with `git worktree add <program-dir>/worktrees/<task-id> -b orch/<slug>/<task-id> <base>`, so every host works the same way. A retry or fix round reuses the existing worktree and branch. Then start a worker in the background through the host's native delegation per `HOST-COMPATIBILITY.md`, with the brief from [`references/worker-brief.md`](references/worker-brief.md) naming that worktree. On Claude Code that is the Agent tool with `run_in_background: true` and no `isolation`, because the worktree already exists. On Codex, use the subagent tool its live schema exposes. A host without background delegation runs one task at a time. Record the worker in a decision row. A `can-stack:` or `restack:` line follows [`references/stacks.md`](references/stacks.md).

**On a worker report.** Read the diff, the PR, and the checks yourself. The summary is a claim, the diff is the evidence.

- `PASS` with an open PR and green checks at a named head: set `pr` and `head`, move to `verifying`, and start the lanes the task's level requires at that head SHA, with the briefs in [`references/verification.md`](references/verification.md).
- `ISSUES` or `BLOCKED`: retry by cause with a fresh worker carrying the consolidated scope (original brief, the report, the branch). Use a smaller scope after a context limit, the same brief after a dropped run, and the `hardest-tasks` role after a capability failure. After two failed attempts, move the task to `parked` and raise it at the next user message.

**On lane verdicts.** Wait for every lane of the task. A verdict covers one head SHA.

- Every lane `PASS` at the same head: record each verdict in `verdict`, then move to `merging`.
- Any `ISSUES`: triage per `references/verification.md` first. Non-blocking findings go to `findings.md`. With blocking findings left, move to `building` and start a fresh worker with the fix-round brief from `references/worker-brief.md`, then verify the fix with the fix-round lanes. When `program.py` refuses the move because the fix budget is spent, park the task instead.
- `STALE`: the head moved. Reconcile the task with its live PR, then rerun the lanes at the new head.

**Merge one PR at a time.** Merges are the one serialized step. Under `stop-at-verified`, stop at `merging` and list the PR for the user. Under `merge`:

1. Fetch main. Ask whether what landed since the PR's base can affect it: a conflict, a file both sides changed, or changed code the PR calls. When it can, send a fresh worker to rebase and get checks green, then rerun the lanes the rebase rule in `references/verification.md` names. When it cannot, merge without a rebase.
2. Merge through the **merge-when-ci-passes** skill at the verified head. A code repair it would make goes to a fresh worker on that branch instead, so you never edit code.
3. Move the task to `merged` and remove its worktree with `git worktree remove`. Run `program.py ready` again, because a merge can unblock dependents and leaves stacked children to restack.

**Record every event** as one decision row: what happened, why, evidence (PR, SHA, path), result. Copy each worker's out-of-scope problems into `findings.md` with the task that found it. Judge a worker by its pushes and PR activity, not its status text.

## 5. Talk to the user

The user may write at any time while workers run. Answer from the program directory and live PR state.

- **Status** ("co się dzieje", "catch me up"): follow the **ketchup** skill with the program directory as its record of what changed. Embed the task's screenshots from `screenshots/<task-id>/`.
- **New rule** ("use skill X for the frontend"): add it to `program.md`. It applies to every brief started after it.
- **Hold or stop**: stop every running worker, record each one's last pushed SHA, and start no new work until the user releases the hold.

## 6. Close the program

The program is settled when `program.py show` prints `program: settled`. When at least one task merged, run the **thermo-nuclear-code-quality-review** skill once, as one `verify-audit` unit, over the range from main at program start to the current main. Its findings never start a fix round. Add them to `findings.md` as candidate refactoring issues. Then follow the **ketchup** skill for the final report. It covers what merged with links, what is parked and why, problems found and how each was solved, the screenshots, and `findings.md` as proposed new issues, with the thermo-nuclear findings grouped as refactoring candidates. Create an issue only on the user's yes, through the tracker in `docs/agents/issue-tracker.md`.

## Reply

Restate the goal, then per task its live state, verdict, and PR link, what merged, what is parked and its reason, open gates waiting on the user, and the follow-ups proposed from `findings.md`.
