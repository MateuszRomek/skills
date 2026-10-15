# Agent Mode

This is my personal collection of skills for building software with coding agents. It covers planning, implementation, verification, review, and local delivery.

Agent Mode is heavily inspired by [pstack](https://github.com/cursor/plugins/tree/main/pstack) by [Lauren Tan](https://x.com/poteto) and [Matt Pocock's skills](https://github.com/mattpocock/skills) by [Matt Pocock](https://x.com/mattpocockuk).

Lauren also wrote an excellent [guide to pstack](https://x.com/poteto/status/2094457600259842065). I recommend reading it to understand the ideas behind this workflow.

## Quick start

1. Install the skills in your project:

   ```bash
   npx skills add MateuszRomek/skills
   ```

   The installer asks which skills and which agents you want.

2. Open your project in your coding agent and run both setup skills once:

   | Host | Run |
   | --- | --- |
   | Claude Code | `/setup-agent-mode`, then `/setup-engineering-workspace` |
   | Codex | `$setup-agent-mode`, then `$setup-engineering-workspace` |

3. Commit the files the setup skills created, so teammates and cloud environments get the same configuration.

4. Describe your task. With the session hook on, the agent enters Agent Mode by itself for multi-file changes, design choices, unclear bugs, and performance work. You can still start it explicitly with `/agent-mode` (or `$agent-mode` in Codex).

## The setup skills

Both setup skills are interactive. They look at your project, ask a few short questions, show you what they plan to write, and write files only after you confirm. You can run them again at any time to change your answers.

### `setup-agent-mode`: choose which models do the work

**Use case:** Many skills split work across subagents, for example several reviewers checking a change or several competing designs in `arena`. This skill decides which model and reasoning effort each of those jobs uses, and how many subagents may run.

**What it does:**

1. Copies the shared Agent Mode files into `.agents/agent-mode/`.
2. Detects your host (Claude Code or Codex) and the models it can use.
3. Asks what you care about: best quality, balanced, lowest cost, or speed. It also asks how you pay and which models you prefer or want to avoid.
4. Researches the eligible models and recommends a model and effort for every role, with a cheaper and a stronger alternative.
5. Proposes limits: total subagents per task, how many run at once, and how deep delegation may nest.
6. Writes the profile you confirm and validates it.
7. Asks whether to install the session hook, which is on by default. The hook loads a short routing instruction at the start of every session and again after compaction, so you do not invoke `agent-mode` on every prompt. Codex runs the hook only after you approve it in `/hooks`.
8. Optionally offers to create a project verification skill with `create-verification-skill`.

**What it produces:**

```text
.agents/agent-mode/
  HOST-COMPATIBILITY.md     how skills adapt to each host
  ROUTING.md                the list of roles that can be delegated
  agents/                   shared agent definitions
  session-start.md          routing instruction the session hook prints
  models.claude-code.yaml   your profile for Claude Code
  models.codex.yaml         your profile for Codex
```

Each host gets its own `models.<host>.yaml`, so run the skill once in every host you use. A profile looks like this:

```yaml
version: 2
host: codex
intent:
  optimization: "Quality with restrained usage"
  budget: "none"
delegation:
  mode: enabled
  max-workers-per-task: 8
  max-concurrent-workers: 3
  max-delegation-depth: 1
roles:
  feature:
    execution: coordinator   # the main agent does this work itself
  reviewer:
    execution: workers       # this work goes to subagents
    workers:
      - model: <model-id>
        reasoning: low
```

**Good to know:**

- Without a valid profile, skills start no subagents. Work that the main agent can do still runs; workflows that need independent workers, such as `arena` and `interrogate`, report that they are unavailable.
- Ask for the `global` scope to write a personal profile to `~/.agents/agent-mode/` instead. It applies to every repository on that machine that has no profile of its own. A repository profile always wins over the global one.
- Setup never commits or pushes. Commit the project profile yourself.

### `setup-engineering-workspace`: connect your issue tracker and docs

**Use case:** The planning skills (`to-spec`, `to-tickets`, `triage`, `wayfinder`, and others) create and read issues and project documentation. This skill tells them where those live in your project.

**What it does:**

1. Checks your git remote, `CLAUDE.md` or `AGENTS.md`, and any existing `CONTEXT.md` or ADRs.
2. Asks where you track issues: GitHub, GitLab, local markdown files under `.scratch/`, or another tool you describe (Jira, Linear, and so on).
3. If the `triage` skill is installed, asks whether to keep the default triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.
4. Picks a domain documentation layout: one `CONTEXT.md` and `docs/adr/` at the root, or one `CONTEXT.md` per package in a monorepo.
5. Shows you a draft and writes it after you confirm.

**What it produces:**

```text
docs/agents/
  issue-tracker.md    where issues live and how to create them
  triage-labels.md    label names (only when triage is installed)
  domain.md           where CONTEXT.md and ADRs live
CLAUDE.md or AGENTS.md
  a short "## Agent skills" section that points to the files above
```

You can edit these files directly later. Run the skill again only to switch issue trackers or start over.

## Using Agent Mode

`agent-mode` is the entry point. Describe your task, and it picks a playbook, loads the relevant engineering principles, and calls the right skills. A typical feature goes like this:

```text
idea or specification
  -> how                    understand the existing code
  -> architect or arena     compare designs, when choices remain
  -> implementation         in small, verified slices
  -> interrogate            adversarial review, when the risk warrants it
  -> prepare-pull-request   only after you approve
  -> merge-when-ci-passes   only after you approve
```

Skills never commit, push, open a pull request, or merge unless you explicitly ask.

## What is included

- **Main router:** `agent-mode` and its task playbooks.
- **Understanding and design:** `how`, `why`, `architect`, `arena`, `research`.
- **Planning** (adapted from Matt Pocock): `grilling`, `domain-modeling`, `wayfinder`, `to-spec`, `to-tickets`, `triage`.
- **Implementation:** `implement-specification`, `tdd`.
- **Verification and review:** `create-verification-skill`, `interrogate`, `swarm`, `blast-radius`, `benchmark-checklist`.
- **Learning from mistakes:** `correct`, `reflect`.
- **Delivery:** `prepare-pull-request`, `merge-when-ci-passes`, `resolving-merge-conflicts`.
- **Engineering principles:** the `principle-*` skills.
- **Writing:** `copywriting` and `copy-editing` (adapted from [Corey Haines's marketingskills](https://github.com/coreyhaines31/marketingskills)), `technical-writing`, `writing-for-agents`.

To see every skill before installing, run `npx skills add MateuszRomek/skills --list`.

## More install options

```bash
# Install every skill for Claude Code and Codex without prompts
npx skills add MateuszRomek/skills --agent codex claude-code --skill '*'

# Same, but globally instead of in the current project
npx skills add MateuszRomek/skills --global --agent codex claude-code --skill '*'

# Update installed skills
npx skills update
```

The skills are used daily in Claude Code and Codex. The [`skills` CLI](https://github.com/vercel-labs/skills) can also install them into Cursor, Antigravity, and other agents. Host differences such as delegation, structured questions, and model selection are handled in [`HOST-COMPATIBILITY.md`](.agents/agent-mode/HOST-COMPATIBILITY.md).

## Contributing

Every skill lives at `.agents/skills/<skill-name>/SKILL.md`, and that folder is the source of truth. To make Claude Code sessions in this repository see the skills, create a local symlink:

```bash
ln -s ../.agents/skills .claude/skills
```

The symlink is gitignored on purpose. Committing it makes `npx skills update` skip the skills in consuming projects.

## License

My original work is available under the [MIT License](LICENSE). The repository preserves third-party MIT license notices in [`.agents/LICENSES`](.agents/LICENSES) and records their sources in [`.agents/THIRD_PARTY_NOTICES.md`](.agents/THIRD_PARTY_NOTICES.md).
