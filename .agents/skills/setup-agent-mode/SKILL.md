---
name: setup-agent-mode
description: "Set up Agent mode globally or in one repository: install its skills and shared files, interview model preferences, research current model docs and pricing, recommend the model and reasoning effort for each role, then write the delegation profile, the Claude Code worker agents, and the session hooks. Use for /setup-agent-mode, configure agent mode, choosing models for agent roles, changing its execution profile, or turning automatic Agent mode routing on or off."
---

# Setup Agent mode

Set up Agent mode for one **scope**, `global` or `repo`, and install every piece that scope needs. The scope decides every path in this skill. Read paths from the table below, never from memory.

| Piece | `global` | `repo` |
| --- | --- | --- |
| Agent mode skills | `~/.agents/skills`, via `npx skills add MateuszRomek/skills -g` | `.agents/skills`, via `npx skills add MateuszRomek/skills` |
| Shared files (`<agent-mode-dir>`) | `~/.agents/agent-mode` | `.agents/agent-mode` |
| Profile | `~/.agents/agent-mode/models.<host>.yaml` | `.agents/agent-mode/models.<host>.yaml` |
| Claude Code workers | `$CLAUDE_CONFIG_DIR/agents` (default `~/.claude/agents`) | `.claude/agents` |
| Session hooks | `$CLAUDE_CONFIG_DIR/settings.json`, `$CODEX_HOME/hooks.json` | `.claude/settings.json`, `.codex/hooks.json` |
| Verification skill | not offered | offered in step 14 |

A `global` setup touches nothing in the current repository. A `repo` setup touches nothing in the home directory, and its files are meant to be committed. When both exist, the repository profile wins for that checkout. The selected profile is the only persistent source of delegation limits, worker counts, models, reasoning efforts, and inheritance choices. [`assets/agent-mode/ROUTING.md`](assets/agent-mode/ROUTING.md) defines only the stable role names and their work semantics; it contains no execution defaults.

## Steps

### 1. Choose the scope

Ask the user which scope to set up, unless their request already names it. Explain the choice in one line each: `global` gives the same setup in every repository on this machine, and `repo` puts the setup in this repository so teammates and cloud environments get it from git. Recommend `global` for a personal setup. Detect what already exists in both scopes, using the table, and show it with the question.

Complete this step when the user has named one scope. Use that scope for every later step.

### 2. Install the Agent mode skills

Check the scope's skills directory for `agent-mode` and the skills its playbooks route to. When any is missing, show the scope's install command and run it after the user confirms. The installer asks which skills and which agents to install.

Complete this step when `agent-mode` exists in the scope's skills directory.

### 3. Install the shared Agent mode files

Read [`assets/agent-mode/HOST-COMPATIBILITY.md`](assets/agent-mode/HOST-COMPATIBILITY.md). Copy the contents of `assets/agent-mode` from this skill directory to the scope's `<agent-mode-dir>`. Create the destination when it does not exist. Refresh the shared reference and agent definitions on every run, but preserve every existing `models.*.yaml` profile.

For the `repo` scope, keep `.agents/agent-mode/models.<host>.yaml` trackable by git. If an ignore rule covers it, narrow that rule or add a profile-specific exception. Do not change unrelated ignore rules.

Complete this step when the destination's `HOST-COMPATIBILITY.md`, `ROUTING.md`, `session-start.md`, both files under `agents`, and both scripts under `hooks` match the packaged assets.

### 4. Detect the host and available models

Resolve the host through the reference above. If the runtime does not identify itself, ask the user which host runs this session before writing a host-specific file.

The host decides which models exist for this profile. Some hosts route only their own vendor's models, such as Claude Code with Anthropic models and Codex with OpenAI models. Others front several providers, such as T3 Code. Build the host's model catalog from these sources, in order:

1. The live delegation-tool schema or model catalog. It is authoritative.
2. The host's own documentation, when the live schema lists no models. Research it with the host protocol in [`references/model-advisor.md`](references/model-advisor.md).
3. The user, who confirms every identifier that came from documentation, because documentation can lag the installed version.

The catalog is done when you know which providers the host reaches, every assignable model identifier, the reasoning efforts per model, and whether a subagent can run a different model from its parent. If no source yields identifiers, the only eligible worker assignment to propose is `inherit-parent`, and the user must still confirm it. Never write an identifier that neither the live schema nor the user confirmed.

Record which controls the host exposes. These may include model, reasoning effort, concurrency, and a per-agent token budget. Do not promise a control the host cannot enforce. Account count is not a routing field unless the host exposes account selection directly.

### 5. Interview the user about models

Ask before researching or proposing. Use one compact structured question when the host supports it. Otherwise ask concise questions in chat. Skip anything the user already supplied.

Cover these decisions:

- what to optimize for, such as strongest results, balanced quality and cost, lowest practical cost, lowest latency, or a custom split by role;
- how the user pays: API tokens, a subscription plan with usage limits, or both;
- the spend or usage budget and its unit, such as per top-level run, per delegated worker, or per day, when the user has a real limit;
- which host-confirmed models the user prefers, wants for a specific job, or wants excluded, and the reason for each preference;
- whether delegation is enabled at all.

Record each stated preference with its reason. A preference outranks a heuristic in the recommendation.

The interview is done when you know the optimization goal, the billing model, the eligible model set, and every stated preference. Leave limits and rosters to step 8, where you recommend them.

### 6. Research the eligible models

Read [`references/model-advisor.md`](references/model-advisor.md). Research every model in the host catalog that the user left eligible, with the model protocol it defines, then classify every role in `ROUTING.md` into its demand classes. The live host catalog still decides which identifiers are valid. Research decides which valid identifier fits each role.

### 7. Load current state

The write target is the scope's profile. Load it when it exists. When it is absent, load the active profile selected by `HOST-COMPATIBILITY.md` as the starting proposal. This lets a profile from the other scope seed the first one in this scope without changing its assignments or deleting it.

Show the write target and the active profile separately. If a higher-precedence profile exists while writing a lower one, name it and explain that this checkout will keep using it. For example, a repository profile masks the global profile.

Treat a version 2 profile as the current proposal to review, not proof that its tradeoffs still match the user's goal. Compare its assignments with the research and flag each one the research no longer supports. Treat every earlier version as unconfigured: it may inform a proposal, but every limit and route must be reconfirmed before writing version 2. Until then, Agent mode starts no workers.

### 8. Recommend and confirm

Present the recommendation in the format `references/model-advisor.md` defines: every role with its class, execution, model, effort, relative cost, and a one-clause reason, followed by a cheaper and a stronger alternative and the research sources. Keep it inside the eligible model set and budget. If the budget cannot support the requested quality, say so and offer the smallest useful adjustment.

Recommend the delegation limits with it:

- the maximum total number of subagent starts in one top-level task, including every nested workflow;
- the maximum number of concurrently active subagents in that task;
- the maximum delegation depth, where `1` allows only root-owned starts and `unlimited` leaves depth unrestricted;
- the roster length of every `workers` route, and any host-supported per-worker budget controls.

Show the write scope and path and mark stale identifiers. Ask the user to confirm or revise the complete profile. Recommendations are proposals, not defaults. Write no limit, roster, model, effort, inheritance, or coordinator route until the user confirms it. `inherit-parent` is valid only when the user explicitly selects it for that roster entry.

### 9. Validate

The file's top-level `host` must equal the resolved host slug. Every explicit model and reasoning effort must be supported by the current host. An explicitly selected `inherit-parent` entry passes structural validation. Reject unavailable combinations before writing. Run `python3 <skill-dir>/scripts/validate-profile.py <profile-path> <agent-mode-dir>/ROUTING.md`. Then run `python3 <skill-dir>/scripts/audit-routing.py <agent-mode-dir>`. Structural validation checks the version 2 contract; live host validation remains the authority for model identifiers and reasoning efforts.

### 10. Write the rule

Write the confirmed profile to the scope's profile path so reruns stay idempotent. Preserve every other profile and every unrelated file. Use this shape:

```yaml
version: 2
host: <resolved-host-slug>
intent:
  optimization: <confirmed-routing-goal>
  budget: <confirmed-limit-with-unit-or-none>
delegation:
  mode: enabled
  max-workers-per-task: <confirmed-positive-integer-or-unlimited>
  max-concurrent-workers: <confirmed-positive-integer-or-host-limit>
  max-delegation-depth: <confirmed-positive-integer-or-unlimited>
roles:
  feature:
    execution: coordinator
  how-explorer:
    execution: workers
    workers:
      - model: <confirmed-model-id>
        reasoning: <confirmed-reasoning-effort>
  arena-runners:
    execution: workers
    workers:
      - model: <confirmed-model-id>
        reasoning: <confirmed-reasoning-effort>
```

The angle-bracketed values describe the schema. Replace them with user-confirmed, host-validated values. Quote intent strings when YAML could interpret them as another type. Include every role listed in `ROUTING.md` when delegation is enabled. A `coordinator` route has no `workers`. A `workers` route has a non-empty roster, and that list is the complete configured capacity for one invocation of the role. To disable all delegation, keep `intent`, write only `mode: disabled` inside `delegation`, and omit `roles` and all limits. Do not maintain another role list here.

### 11. Pin Claude Code workers

Skip this step for every host other than `claude-code`. Claude Code's delegation tool selects a model but not a reasoning effort, so each `model` and `reasoning` pair in the profile needs its own subagent definition. Run `python3 <skill-dir>/scripts/claude-agents.py <scope>` from the repository, with the same scope as the profile. It writes one `am-<model>-<reasoning>.md` per pair to the scope's workers directory. It removes `am-*` definitions it wrote earlier that the profile no longer routes to, and keeps every other agent file. Report the agent names it prints.

### 12. Route sessions into Agent mode

Ask whether every new session should load the Agent mode routing instruction. The default is on. A `SessionStart` hook prints `session-start.md` from the shared files on startup, resume, clear, and compact, so the user does not invoke `agent-mode` on every prompt. The hook reads the file on each run, so a refreshed `session-start.md` takes effect without touching the hook.

Run `python3 <skill-dir>/scripts/session-hook.py <host> <scope> <on|off>` from the repository, with the same scope as the profile. It merges one hook entry into the host's settings file and keeps every other hook. For `claude-code` it also installs two hooks from the shared `hooks` directory. A `PostToolUse` hook on `Skill` records that `agent-mode` ran in the session, and a `UserPromptSubmit` hook then reminds every later prompt to keep following the skill. `off` removes all three. Reruns replace the entries instead of adding more. The settings files are the scope's session hooks row.

Codex runs a new or changed hook only after the user approves it in `/hooks`. Tell the user to open `/hooks` in Codex and approve the Agent mode entry. If a `repo` hook is missing from `/hooks`, the user marks the project trusted in Codex first. Codex keeps the approval while the hook command is unchanged, so editing `session-start.md` needs no new approval. For any other host, report that it has no supported hook and offer to add the contents of `session-start.md` to the host's standing instruction file instead.

### 13. Confirm

Show the host, delegation mode, optimization goal, budget or cost posture, total task worker limit, concurrency limit, delegation depth, file path, coordinator roles, explicit worker rosters, intentionally inherited entries, any unavailable combinations rejected during setup, and the Claude Code worker agents written in step 11, and the session hook state with the settings file it changed. Then list every row of the scope table with its path and state for the chosen scope. Run `python3 <skill-dir>/scripts/select-profile.py <host>` from the repository and report the scope and path it prints. Say whether a higher-precedence profile masks the one just written. Re-running this skill updates only the selected scope for the current host. A project profile is ready for the user's commit and push; setup itself does not stage, commit, or push it. A global profile stays on this machine, so cloud environments do not receive it.

Complete this step when every row is installed, or marked not applicable with its reason, such as the workers row on a host other than Claude Code.

### 14. Offer a verification skill (optional)

Skip this step for the `global` scope. Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill` from its installed location. On no, move on without pushing.
