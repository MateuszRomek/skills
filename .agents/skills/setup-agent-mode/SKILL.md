---
name: setup-agent-mode
description: Configure host-local Agent mode models, reasoning efforts, and panel sizes. Detects the current agent host and writes its local routing file. Use for /setup-agent-mode, "configure agent mode models", or changing the workflow's cost profile.
---

# Setup Agent mode

Install the shared Agent mode files in the current repository, then write `.agents/agent-mode/models.<host>.local.yaml` for the current coding-agent host. The model file stays local to this machine and overrides inherited-model defaults without coupling other hosts to its model identifiers.

## Steps

### 1. Install the shared Agent mode files

Read [`assets/agent-mode/HOST-COMPATIBILITY.md`](assets/agent-mode/HOST-COMPATIBILITY.md). Copy the contents of `assets/agent-mode` from this skill directory to `.agents/agent-mode` in the current repository. Create the destination when it does not exist. Refresh the shared reference and agent definitions on every run, but preserve every `models.*.local.yaml` file already present.

Ensure that the repository ignores `.agents/agent-mode/models.*.local.yaml`. Do not change unrelated ignore rules.

Complete this step when `.agents/agent-mode/HOST-COMPATIBILITY.md` and both files under `.agents/agent-mode/agents` match the packaged assets.

### 2. Detect the host and available models

Resolve the host through the reference above. If the runtime does not identify itself, ask the user to select the host before writing a host-specific file. Enumerate models and reasoning efforts the host can actually assign to a subagent. Prefer the host's live model catalog or delegation-tool schema over documentation or memory. If model detection is unavailable, configure only `inherit-parent`. Never write an identifier that the current host has not confirmed.

### 3. Load current state

Load `.agents/agent-mode/models.<host>.local.yaml` when it exists. Otherwise start with inherited models, one worker for single-worker roles, and two workers for comparison panels.

### 4. Map and confirm

Show every role with its model, reasoning effort, and worker count. Mark stale identifiers. Use the host's structured-question capability when available. The panel length sets fan-out for `how-critics`, `arena-runners`, `architect-runners`, and `interrogate-reviewers`. `arena-cross-judge` is one worker chosen from its list, preferably from a different model family. `swarm-worker` is reused for each worker unless a race assigns models per arm.

### 5. Validate

The file's top-level `host` must equal the resolved host slug. Every explicit model and reasoning effort must be supported by the current host. `inherit-parent` always passes. Reject unavailable combinations before writing.

### 6. Write the rule

Overwrite `.agents/agent-mode/models.<host>.local.yaml` so reruns stay idempotent. Use this shape:

```yaml
version: 1
host: codex
roles:
  feature:
    - model: inherit-parent
      reasoning: inherit-parent
  how-explorer:
    - model: inherit-parent
      reasoning: inherit-parent
  how-critics:
    - model: inherit-parent
      reasoning: inherit-parent
    - model: inherit-parent
      reasoning: inherit-parent
  arena-runners:
    - model: inherit-parent
      reasoning: inherit-parent
    - model: inherit-parent
      reasoning: inherit-parent
  arena-cross-judge:
    - model: inherit-parent
      reasoning: inherit-parent
  interrogate-reviewers:
    - model: inherit-parent
      reasoning: inherit-parent
    - model: inherit-parent
      reasoning: inherit-parent
```

Include every supported role in the real file: `feature`, `refactoring`, `bug-fix`, `perf-issue`, `hillclimb`, `judgment-prose`, `hardest-tasks`, `how-explorer`, `how-explainer`, `how-critics`, `why-investigators`, `why-synthesizer`, `reflect-tooling`, `reflect-judgment`, `arena-runners`, `arena-cross-judge`, `swarm-worker`, `architect-runners`, and `interrogate-reviewers`.

### 7. Confirm

Show the host, file path, panel fan-out, explicit models, inherited roles, and any unavailable combinations rejected during setup. Re-running this skill updates only the current host's file.

### 8. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill` from its installed location. On no, move on without pushing.
