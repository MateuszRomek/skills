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

Record which controls the host exposes. These may include model, reasoning effort, worker count, and a per-agent token budget. Do not promise a hard token limit when the host only exposes model and reasoning controls.

### 3. Learn the user's routing goal

Before proposing assignments, establish the choices that materially change the profile. Use one compact structured question when the host supports it. Otherwise ask concise questions in chat. Do not ask for information the user already supplied.

Cover these decisions:

- what to optimize for, such as strongest results, balanced quality and cost, lowest practical cost, lowest latency, or a custom split by role;
- the token or spend budget and its unit, such as per top-level run, per delegated worker, or per day, when the user has a real limit;
- whether every host-confirmed model and reasoning effort is eligible, or the profile must use a restricted set;
- acceptable comparison-panel fan-out, because worker count often changes cost more than a single model choice;
- any roles that should deliberately inherit the parent because their work must match the parent or because the parent changes often.

If the user does not know what to choose, recommend a concrete profile from the live host catalog. Explain the main quality, latency, and cost tradeoff in plain language, then ask for confirmation. Do not make the user translate model names into a routing strategy.

`inherit-parent` is not the default answer when the host exposes explicit model routing. Use it only when the user chooses inheritance for a role, the parent is intentionally the best fit, or live capability detection cannot validate an explicit assignment.

### 4. Load current state

Load `.agents/agent-mode/models.<host>.local.yaml` when it exists. Treat it as the current profile to review, not proof that its tradeoffs still match the user's goal. On first setup, start from the user's confirmed goal and the live model catalog. Use one worker for single-worker roles and the confirmed panel fan-out for comparison roles.

### 5. Recommend, map, and confirm

Propose explicit assignments supported by the active host. Match stronger reasoning to ambiguous, cross-cutting, algorithmic, and judgment-heavy roles. Match cheaper or faster models to narrow exploration, mechanical checks, and high-fan-out panels. Keep the recommendation inside the confirmed model set and budget. If the requested budget cannot support the requested quality or fan-out, say so and offer the smallest useful adjustment.

Show every role with its model, reasoning effort, worker count, and a short reason for any non-obvious assignment. Mark stale identifiers. Ask the user to confirm or revise the proposed map before writing it. The panel length sets fan-out for `how-critics`, `arena-runners`, `architect-runners`, and `interrogate-reviewers`. `arena-cross-judge` is one worker chosen from its list, preferably from a different model family. `swarm-worker` is reused for each worker unless a race assigns models per arm.

### 6. Validate

The file's top-level `host` must equal the resolved host slug. Every explicit model and reasoning effort must be supported by the current host. `inherit-parent` always passes. Reject unavailable combinations before writing.

### 7. Write the rule

Overwrite `.agents/agent-mode/models.<host>.local.yaml` so reruns stay idempotent. Use this shape:

```yaml
version: 1
host: <resolved-host-slug>
roles:
  feature:
    - model: <confirmed-model-id>
      reasoning: <confirmed-reasoning-effort>
  how-explorer:
    - model: <confirmed-model-id>
      reasoning: <confirmed-reasoning-effort>
  how-critics:
    - model: <confirmed-model-id>
      reasoning: <confirmed-reasoning-effort>
    - model: <confirmed-model-id>
      reasoning: <confirmed-reasoning-effort>
  arena-runners:
    - model: <confirmed-model-id>
      reasoning: <confirmed-reasoning-effort>
    - model: <confirmed-model-id>
      reasoning: <confirmed-reasoning-effort>
  arena-cross-judge:
    - model: <confirmed-model-id>
      reasoning: <confirmed-reasoning-effort>
  interrogate-reviewers:
    - model: <confirmed-model-id>
      reasoning: <confirmed-reasoning-effort>
    - model: <confirmed-model-id>
      reasoning: <confirmed-reasoning-effort>
```

The angle-bracketed values describe the schema. Replace them with validated host values. Use `inherit-parent` only for an intentionally inherited role or a required fallback.

Include every supported role in the real file: `feature`, `refactoring`, `bug-fix`, `perf-issue`, `hillclimb`, `judgment-prose`, `hardest-tasks`, `how-explorer`, `how-explainer`, `how-critics`, `why-investigators`, `why-synthesizer`, `reflect-tooling`, `reflect-judgment`, `arena-runners`, `arena-cross-judge`, `swarm-worker`, `architect-runners`, and `interrogate-reviewers`.

### 8. Confirm

Show the host, optimization goal, budget or cost posture, eligible model set, file path, panel fan-out, explicit models, intentionally inherited roles, and any unavailable combinations rejected during setup. Re-running this skill updates only the current host's file.

### 9. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill` from its installed location. On no, move on without pushing.
