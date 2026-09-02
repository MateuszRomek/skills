---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

- The user said "reflect" or "/reflect".
- A complex task (5+ tool calls) just landed cleanly and the recipe is worth keeping.
- The agent hit dead ends, found the working path, and the path generalizes.
- The user corrected the agent's approach mid-task.
- A non-trivial workflow emerged that isn't captured anywhere.

Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

Resolve host capabilities and the active profile through [`HOST-COMPATIBILITY.md`](../../agent-mode/HOST-COMPATIBILITY.md) before reading history or delegating.

### 1. Locate the active transcript

Use the active host's task or conversation API when available. Otherwise use only the workspace-scoped transcript location supplied by the host. Never scan unrelated projects. If neither source exists, write a tight digest of the visible session and use that.

```bash
ls -t <agent-transcripts>/*.jsonl <agent-transcripts>/*/*.jsonl <agent-transcripts>/*/subagents/*.jsonl 2>/dev/null | head -10
```

When the host supplies JSONL transcripts, account for flat, nested, and subagent layouts.

For each candidate, read the first JSONL line and check that `message.content[0].text` contains the conversation's opening user prompt. Take the matching path. If no path resolves, write a tight digest of the session and pass that instead.

### 2. Spawn three reviewers in parallel

Launch three reviewers together through the host's native delegation capability. Use the active profile for role overrides. Reviewers may need MCP access for cited context, so give them the least-permissive sandbox that preserves those tools. Their prompts forbid file writes; the parent applies edits.

| Lens | `model` | Prompt template |
|---|---|---|
| Judgment | `reflect-judgment`, otherwise inherit parent | `references/judgment-reviewer.md` |
| Tooling | `reflect-tooling`, otherwise inherit parent | `references/tooling-reviewer.md` |
| Divergent | `reflect-judgment`, otherwise inherit parent | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings to the parent task.

### 3. Synthesize

Spawn one synthesizer using `reflect-judgment` when configured; otherwise inherit the parent. Preserve MCP access when citation checks need it. Use `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. The synthesizer returns a structured Accepted / Rejected / Backlog list.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. The synthesizer already applies this criterion; this is a final pass before edits land. See the **encode-lessons-in-structure** principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org; do not auto-apply.

Backlog items file to whatever devex / backlog tracker your team uses automatically. Those are tracker submissions, not skill edits. Only the Accepted list waits for approval.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): invoke **skill-creator** and **writing-for-agents**, then run the draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): invoke **skill-creator** and run its description-optimization loop.
- `new skill via skill-creator: <kebab-name>`: invoke **skill-creator**. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done. Skip this step if it doesn't.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
