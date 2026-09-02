# Agent Mode

This is my personal collection of skills for building software with coding agents. It covers planning, implementation, verification, review, and local delivery.

Agent Mode is heavily inspired by [pstack](https://github.com/cursor/plugins/tree/main/pstack) by [Lauren Tan](https://x.com/poteto) and [Matt Pocock's skills](https://github.com/mattpocock/skills) by [Matt Pocock](https://x.com/mattpocockuk).

Lauren also wrote an excellent [guide to pstack](https://x.com/poteto/status/2094457600259842065). I recommend reading it to understand the ideas behind this workflow.

## Install

Use the interactive installer to choose skills and agents:

```bash
npx skills add MateuszRomek/skills
```

After installation, invoke these setup skills once in each project:

```text
$setup-agent-mode
$setup-engineering-workspace
```

`setup-agent-mode` installs the shared files under `.agents/agent-mode` and configures local model routing for the active host. `setup-engineering-workspace` configures the issue tracker, triage labels, and domain documentation used by the planning skills.

To install every skill in the current project for Codex without prompts, run:

```bash
npx skills add MateuszRomek/skills --agent codex --skill '*'
```

To install every skill globally for Codex, run:

```bash
npx skills add MateuszRomek/skills --global --agent codex --skill '*'
```

The [`skills` CLI](https://github.com/vercel-labs/skills) supports Codex, Cursor, Claude Code, Antigravity, and other agents.

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
- verification and review workflows such as `create-verification-skill`, `interrogate`, `swarm`, and `blast-radius`;
- planning skills adapted from Matt Pocock's collection, including `grilling`, `domain-modeling`, `wayfinder`, `to-spec`, and `to-tickets`;
- local delivery skills such as `prepare-pull-request` and `merge-when-ci-passes`;
- reusable engineering principles under `principle-*`.

The repository intentionally excludes skills tied to a specific application library. For example, Better Auth skills should be installed from their upstream source in projects that use Better Auth.

## Repository layout

```text
.agents/
  agent-mode/       Shared host compatibility and agent definitions
  skills/           Flat collection of installable skills
  LICENSES/         Original third-party license notices
```

Every installable skill lives at `.agents/skills/<skill-name>/SKILL.md`. The skill name in its frontmatter matches the directory name.

## License

My original work is available under the [MIT License](LICENSE). The repository preserves third-party MIT license notices in [`.agents/LICENSES`](.agents/LICENSES) and records their sources in [`.agents/THIRD_PARTY_NOTICES.md`](.agents/THIRD_PARTY_NOTICES.md).
