# Host compatibility

Read this reference only when an Agent mode workflow invokes another skill, delegates work, asks a structured question, reads conversation history, waits for future state, or selects a model.

## Resolve the host

Resolve the host from identity supplied by the running product, such as runtime instructions, host metadata, or host-owned tool documentation. Normalize an explicit identity to a stable lowercase slug:

| Runtime identity | Slug |
| --- | --- |
| Codex | `codex` |
| Claude Code | `claude-code` |
| Antigravity | `antigravity` |

A host selected explicitly by the user during `setup-agent-mode` is also resolved. Repository directories, installed CLIs, environment leftovers, and model names are not host identity. If runtime signals conflict or none explicitly identify the product, leave the host unresolved.

Host identity and host capability are separate. Inspect the live tool schema before using delegation, structured input, task history, waiting, or model overrides. A known host does not imply that every installation or session exposes the same tools.

## Skills

Invoke a skill by its catalog name through the host's native skill mechanism. If the host exposes no explicit skill tool, read the target `SKILL.md` and follow it. Repository skills live in `.agents/skills`. Compatibility links may expose the same directories elsewhere, but `.agents/skills` remains the source of truth.

## User input

Use structured questions when the host provides them. Otherwise ask one concise question in chat. Keep permission and approval requests in the host's native approval flow.

## Delegation

Use the host's native subagent capability. Launch independent workers together and wait for every required result before synthesis. Give each worker a bounded task, its own writable location when it edits, the evidence it must return, and a model or reasoning effort only when the host supports that override.

Run against the current local workspace by default. Use a remote or cloud environment only when the user requests it or the workflow cannot run locally. Read-only work should use a read-only sandbox when available. A worker that needs MCP or connector access may need the parent's normal sandbox while remaining instructionally read-only.

## Model routing

After resolving the host, look for `.agents/agent-mode/models.<host>.local.yaml`. The file is machine-local and ignored by git. Use it only when its top-level `host` value exactly matches the resolved slug. An unresolved host, missing file, mismatched `host`, missing role, or unavailable model falls back to the parent model and reasoning effort. Panel roles default to two independent inherited-model workers. Single-worker roles default to one inherited-model worker.

Treat configured model identifiers as host-local. Validate explicit model and reasoning values against the live delegation schema when it exposes them. If the host rejects a value, use inheritance for the current run and report the stale entry. Do not substitute an invented identifier.

## Delegation preflight

Before the first delegation in a top-level Agent mode workflow, report the resolved execution plan in one compact block:

```text
Agent mode preflight
Host: codex (runtime-declared)
Profile: .agents/agent-mode/models.codex.local.yaml
Roles: arena-runners = 2 x gpt-5.6-luna/max; arena-cross-judge = gpt-5.6-terra/high
Fallbacks: none
```

Use `Host: unresolved`, `Profile: none`, and the inherited roles when identity or configuration is unavailable. Name mismatches and stale entries under `Fallbacks`. Emit the preflight once. Nested Agent mode workflows reuse it unless the required roles or capabilities change.

## Conversation history

Prefer the host's task or conversation APIs. Otherwise use the workspace-scoped transcript location supplied by the host. If neither exists, use the visible conversation plus live repository state. Stay inside the active workspace and never scan unrelated project histories.

## Long-running work

Continue inside the current task with the host's native wait or continuation mechanism. Create a scheduled task, recurring automation, or separate background task only when the user explicitly asks for one.
