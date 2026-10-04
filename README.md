# Agent Mode

This is my personal collection of skills for building software with coding agents. It covers planning, implementation, verification, review, and local delivery.

Agent Mode is heavily inspired by [pstack](https://github.com/cursor/plugins/tree/main/pstack) by [Lauren Tan](https://x.com/poteto) and [Matt Pocock's skills](https://github.com/mattpocock/skills) by [Matt Pocock](https://x.com/mattpocockuk).

Lauren also wrote an excellent [guide to pstack](https://x.com/poteto/status/2094457600259842065). I recommend reading it to understand the ideas behind this workflow.

## Supported hosts

The skills are host-neutral and are used daily in both Codex and Claude Code:

| Host | Install target | Invoke a skill | Model profile |
| --- | --- | --- | --- |
| Codex | `--agent codex` | `$skill-name` | `.agents/agent-mode/models.codex.yaml` |
| Claude Code | `--agent claude-code` | `/skill-name` | `.agents/agent-mode/models.claude-code.yaml` |

Antigravity is also recognized by Agent mode, and the [`skills` CLI](https://github.com/vercel-labs/skills) can install the collection into Cursor and other agents. Host-specific behavior such as delegation, structured questions, and model selection is resolved at runtime through [`HOST-COMPATIBILITY.md`](.agents/agent-mode/HOST-COMPATIBILITY.md), so a skill never assumes one host's tools.

## Install

Use the interactive installer to choose skills and agents:

```bash
npx skills add MateuszRomek/skills
```

After installation, invoke these setup skills once in each project:

```text
$setup-agent-mode               # Codex
/setup-agent-mode               # Claude Code
$setup-engineering-workspace    # Codex
/setup-engineering-workspace    # Claude Code
```

`setup-agent-mode` installs the shared files under `.agents/agent-mode` and configures project model routing for the active host. `setup-engineering-workspace` configures the issue tracker, triage labels, and domain documentation used by the planning skills.

Setup writes `.agents/agent-mode/models.<host>.yaml` by default, one profile per host. Run `setup-agent-mode` once in each host you use; a Codex profile and a Claude Code profile live side by side, and each host only reads its own. Commit and push this profile with your project so other checkouts, including cloud environments, receive the configured roles, model assignments, and delegation limits. Setup does not commit or push files itself.

For a machine-specific configuration, explicitly request a local override during setup. It writes `.agents/agent-mode/models.<host>.local.yaml`, which remains ignored by git. Skills select the complete local profile when present and otherwise use the project profile. An invalid local profile blocks delegation rather than falling through. Each environment validates the selected profile against its live host capabilities before delegating.

To install every skill in the current project for both Codex and Claude Code without prompts, run:

```bash
npx skills add MateuszRomek/skills --agent codex claude-code --skill '*'
```

To install every skill globally instead, add `--global`:

```bash
npx skills add MateuszRomek/skills --global --agent codex claude-code --skill '*'
```

List a single agent after `--agent` to target only one host.

To inspect the available skills before installation, run:

```bash
npx skills add MateuszRomek/skills --list
```

To update installed skills, run:

```bash
npx skills update
```

## Use Agent Mode

`agent-mode` is the main router. It classifies the task, selects a playbook, loads the relevant engineering principles, and routes work to supporting skills.

A typical feature can move through this sequence:

```text
idea or specification
  -> how
  -> architect or arena when design choices remain
  -> implementation in verified slices
  -> interrogate for adversarial review when risk warrants it
  -> prepare-pull-request after explicit approval
  -> merge-when-ci-passes after explicit approval
```

The workflow keeps local implementation separate from delivery. A skill does not gain permission to commit, push, open a pull request, or merge only because it implemented or verified a change.

## What is included

The collection includes:

- `agent-mode` and its task playbooks;
- architecture and exploration skills such as `how`, `why`, `architect`, and `arena`;
- implementation workflows such as `implement-specification` and `tdd`;
- verification and review workflows such as `create-verification-skill`, `interrogate`, `swarm`, `blast-radius`, and `benchmark-checklist`;
- `correct`, which turns repeated agent mistakes into architecture, types, and checks;
- planning skills adapted from Matt Pocock's collection, including `grilling`, `domain-modeling`, `wayfinder`, `to-spec`, and `to-tickets`;
- local delivery skills such as `prepare-pull-request` and `merge-when-ci-passes`;
- reusable engineering principles under `principle-*`;
- marketing writing skills `copywriting` and `copy-editing`, adapted from [Corey Haines's marketingskills](https://github.com/coreyhaines31/marketingskills).

The repository intentionally excludes skills tied to a specific application library. For example, Better Auth skills should be installed from their upstream source in projects that use Better Auth.

## Repository layout

```text
.agents/
  agent-mode/       Shared host compatibility and agent definitions
  skills/           Flat collection of installable skills
  LICENSES/         Original third-party license notices
.claude/
  skills -> ../.agents/skills
```

Every installable skill lives at `.agents/skills/<skill-name>/SKILL.md`. The skill name in its frontmatter matches the directory name.

`.claude/skills` is a symlink to `.agents/skills`, so Claude Code sessions opened in this repository see the same skills Codex does. `.agents/skills` remains the source of truth; edit skills there.

## License

My original work is available under the [MIT License](LICENSE). The repository preserves third-party MIT license notices in [`.agents/LICENSES`](.agents/LICENSES) and records their sources in [`.agents/THIRD_PARTY_NOTICES.md`](.agents/THIRD_PARTY_NOTICES.md).
