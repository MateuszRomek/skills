---
name: spec-standards-review
description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) on two separate axes: Spec (does the diff do what the issue or spec asked?) and Standards (does it follow this repository's documented coding standards?). Use to review a branch, a PR, or work in progress, or when the orchestrate skill's audit lane runs it."
---

Two-axis review of the diff between `HEAD` and a fixed point:

- **Spec**: does the code faithfully implement the originating issue or spec?
- **Standards**: does the code follow this repository's documented coding standards?

Each axis runs in its own fresh context so one cannot mask the other. This skill aggregates their findings and never reranks them across axes.

## 1. Pin the fixed point

Use the fixed point the caller names: a commit SHA, a branch, a tag, `main`, or `HEAD~5`. When none is named, use the merge-base with the default branch and say so.

Capture the diff command once as `git diff <fixed-point>...HEAD`, and the commit list as `git log <fixed-point>..HEAD --oneline`. Confirm that `git rev-parse <fixed-point>` resolves and the diff is non-empty before going further.

## 2. Find the spec

Look for the originating spec in this order:

1. The issue or spec text the caller passed, such as the source an **orchestrate** brief pastes in full.
2. Issue references in the commit messages, fetched through the tracker that `docs/agents/issue-tracker.md` names.
3. A path the caller passed.
4. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch or feature.

When nothing is found, ask the caller. When there is no spec, skip the Spec axis and report "no spec available".

## 3. Find the standards

List every file in the repository that documents how code should be written. `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`, and `docs/agents/` are on the list when they exist.

The Standards axis always carries this **smell baseline**, a fixed set of Fowler code smells (_Refactoring_, chapter 3) that applies even when the repository documents nothing. A documented repository standard always wins, and where it endorses something the baseline would flag, suppress the smell. Each smell is a labelled judgement call ("possible Feature Envy"), never a hard violation. Skip anything tooling already enforces.

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. Rename it. If no honest name comes, the design is murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file of the change. Extract the shared shape and call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. Move the method onto the data it envies.
- **Data Clumps**: the same few fields or parameters keep travelling together. Bundle them into one type and pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept. Give the concept its own small type.
- **Repeated Switches**: the same `switch` or `if` cascade on the same type recurs across the change. Replace it with polymorphism or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files. Gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. Split it so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. Delete them and inline until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. Hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly delegates onward. Cut it and call the real target directly.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. Drop the inheritance and use composition.

## 4. Run both axes

Dispatch the two axes as two semantic units on the `verify-audit` role through [`HOST-COMPATIBILITY.md`](../../agent-mode/HOST-COMPATIBILITY.md), and wait for both. When the profile keeps the role in the coordinator, run the Spec axis, then the Standards axis, and do not let the first axis's findings shape the second.

**Spec unit.** Give it the diff command, the commit list, and the spec text in full, with this brief:

> Report (a) requirements the spec asked for that are missing or partial, (b) behaviour in the diff the spec did not ask for, and (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding and name the file and lines. Under 400 words.

**Standards unit.** Give it the diff command, the commit list, the standards files from step 3, and the smell baseline pasted in full, with this brief:

> Report (a) every place the diff violates a documented standard, citing the file and the rule, and (b) every baseline smell you spot, named and with the hunk quoted. Mark documented-standard breaches as hard and baseline smells as judgement calls. A documented standard overrides the baseline. Skip anything tooling enforces. Under 400 words.

## 5. Aggregate

Present the two reports under `## Spec` and `## Standards`, verbatim or lightly cleaned. End with one line per axis: its finding count and its worst finding. Do not pick a single worst finding across axes.

Label every finding with its kind so a caller can triage it without rereading:

| Axis | Kind | Meaning |
| --- | --- | --- |
| Spec | `missing` | a requirement the diff does not meet |
| Spec | `wrong` | a requirement implemented incorrectly |
| Spec | `extra` | behaviour the spec did not ask for |
| Standards | `hard` | a breach of a documented repository standard |
| Standards | `judgement` | a baseline smell |
