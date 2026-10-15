---
name: fast-track
description: "Take an idea from loose to published spec and tickets in one run: the agent makes the decisions, asks only about one-way doors, and reports what it decided."
disable-model-invocation: true
---

# Fast track

Run the wayfinder → to-spec → to-tickets pipeline as one owned run. You own the decisions. The human owns only the **one-way doors**, and gets a **decision report** at the end instead of a quiz at every step.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run `/setup-engineering-workspace`.

Start a decision log per the **show-me-your-work** skill at `.audit/<effort-slug>.tsv`. Every decision you make below gets a row.

## Pick the mode

- **Settled.** The conversation already names the destination and the load-bearing decisions. Go to step 3.
- **Fog.** The topic is unexplored, or the user invoked with only a loose idea. Start at step 1.

The user's argument wins when it names a mode. Otherwise pick one and log it.

## Classify every decision

Each open question lands in exactly one class. Classify before you act on it.

- **Fact.** Answerable by reading the repo, docs, or tools. Look it up. Dispatch research per the **research** skill for knowledge outside the working directory.
- **Empirical fork.** Answerable by running something: behavior, layout, timing, perf. Settle it with a throwaway prototype per `../agent-mode/playbooks/prototype.md` and decide from the result.
- **Two-way door.** A product or design call that is cheap to reverse later. Decide it yourself, pick the option the codebase's existing conventions favor, and log the reason.
- **One-way door.** A call that is expensive to reverse or that only the human can make: scope and the destination itself, a user-visible contract, a public API or schema shape, data migration or deletion, security and permission boundaries, cost or vendor choice, anything the user said they care about. Ask.

When unsure between two-way and one-way, ask the question only if a wrong guess would invalidate more than one ticket.

## 1. Name the destination (Fog only)

Read `../wayfinder/SKILL.md` for the vocabulary: destination, frontier, fog of war, out of scope. Explore the codebase and the domain with **domain-modeling**, then draft the destination, the scope boundary, and the full design tree breadth-first.

The step is done when every branch of the design tree is classified.

## 2. Ask one round

Put every one-way door into a single round in the **grilling** format: numbered, each with options and your recommended answer. Ask the destination and scope first if they are one-way doors. Wait for the answers.

A one-way door that only surfaces later (from research or a prototype) goes into one more round at that point. Every other question stays out of the conversation.

## 3. Resolve the tree

Work the tree yourself, frontier first, until no branch is open.

- Run fact lookups and research in parallel through [`HOST-COMPATIBILITY.md`](../../agent-mode/HOST-COMPATIBILITY.md). The active profile decides the worker count.
- Prototype each empirical fork and keep the branch, SHA, or screenshot as evidence.
- Decide each two-way door and log it.

When the tree outgrows one session, chart a wayfinder map on the tracker per `../wayfinder/SKILL.md` and keep resolving its AFK tickets in this run. Record each resolution on its ticket as wayfinder does.

The step is done when every decision has an answer and a log row.

## 4. Write the spec

Follow `../to-spec/SKILL.md` and its template. Choose the test seams yourself and record them under Testing Decisions instead of checking them with the user. Publish it with the `ready-for-agent` label.

## 5. Cut and publish the tickets

Follow `../to-tickets/SKILL.md` steps 1, 2, 3, and 5. Skip step 4's quiz: you own granularity and blocking edges, and you log each non-obvious edge. Publish in dependency order.

## 6. Report

Run the transcript audit from the **show-me-your-work** skill, then reply with the decision report:

1. **Asked.** Each one-way door and the user's answer.
2. **Decided.** Each two-way door you settled: the choice, the alternative you rejected, the reason, and the evidence. Group them by spec section so the user can veto in one pass.
3. **Assumed.** Anything you took as given without evidence.
4. **Published.** The spec and ticket links, the frontier tickets, and the decision log path.

A veto from the user is a change to the spec and the affected tickets. Apply it, log it, and re-report only what changed.

Stop after the report. When the user's invocation also asked to build, continue with the **implement-specification** skill on the published spec.
