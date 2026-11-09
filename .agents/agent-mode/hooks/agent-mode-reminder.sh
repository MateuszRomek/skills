#!/usr/bin/env bash
# Claude Code UserPromptSubmit hook. Silent until agent mode is entered in this session,
# then injects a short reminder on every later prompt.
set -u
input=$(cat)
session=$(printf '%s' "$input" | jq -r '.session_id // empty')
prompt=$(printf '%s' "$input" | jq -r '.prompt // empty')
[ -n "$session" ] || exit 0
marker_dir="${TMPDIR:-/tmp}/claude-agent-mode"
marker="$marker_dir/$session"

case "$prompt" in
  /agent-mode*|"agent mode"*|"agent-mode"*)
    mkdir -p "$marker_dir" && : > "$marker" ;;
esac

[ -f "$marker" ] || exit 0

cat <<'MSG'
<agent-mode-active>
Agent mode is active for this session. Hold to the agent-mode skill, not a paraphrase of it:
- Match the task to a playbook, open its file, and copy its steps verbatim into the todo list before task-specific todos. A skipped step stays listed with a one-line skip reason.
- When a trigger in the skill's table matches, invoke the routed skill through the Skill tool (architect, how, why, interrogate, swarm, arena, figure-it-out, unslop, no-comments, technical-writing). Do not reconstruct it from memory.
- Read the leaf principle-* SKILL.md for every principle you apply, and cite only those in the reply.
- Delegation goes through the active profile that HOST-COMPATIBILITY.md selects (the repository's .agents/agent-mode, else ~/.agents/agent-mode), with its preflight block.
</agent-mode-active>
MSG
