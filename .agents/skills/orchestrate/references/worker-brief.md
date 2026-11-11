# Worker brief

Fill every placeholder and send the result as the worker's whole task. The worker cannot see the program directory's history, its siblings, or this chat. Paste upstream facts in full instead of pointing at them.

```text
Goal of the program: <the user's goal, restated>
Your task: <task id> <title>
Source: <issue URL or spec section, with its full text pasted below>
Done predicate: <the checkable evidence, such as a command and its expected output or a screen state>
Delegation: reserved credits <n or unlimited>. Delegate through the agent-mode skill when your work calls for it.

Rules from the user:
<every rule in program.md, such as the skills to use for frontend work>

Context from dependencies (merged, or the stack parent):
<for each dependency, its PR link and the facts this task relies on>

Worktree: <program dir>/worktrees/<task id>, on branch orch/<slug>/<task id>, created from <main, or for a stacked task the parent's branch at <SHA>>. Run every command there.
Write scope: that worktree, its branch, and <program dir>/screenshots/<task id>/.
Leave every other path untouched, including the rest of <program dir>.

Steps:
1. Follow the agent-mode skill and the playbook it matches for this task. Load it through the host's skill mechanism, which finds it whether it is installed in the repository or globally.
2. Prove the done predicate on the real artifact. For UI work, drive the running app through the app verify skill when one exists and save screenshots of each changed screen to <program dir>/screenshots/<task id>/ with descriptive file names.
3. Review your full diff for correctness. Fix every defect you can show.
4. Review your full diff for security: input validation at boundaries, authorization on every new path, secrets and tokens, injection (SQL, shell, HTML), personal data exposure, unsafe defaults. Fix every finding you can show.
5. Run the no-comments skill on the diff.
6. When the diff changes a feature the app verify skill <name, or none> maps, update that feature's file in its features/ map. When it changes code a formal check covers, run that check, and for an intended change update the verification as its skill says.
7. Commit, push the branch, and open the PR through the prepare-pull-request skill. The program authorizes this PR. Its base is main, or the parent's branch for a stacked task per the orchestrate skill's references/stacks.md.
8. Get the PR's checks green per merge-when-ci-passes steps 1 to 3. Stop before its merge step. The coordinator merges.

Report, in this shape:
Status: PASS | ISSUES | BLOCKED
PR: <url>
Head: <full SHA the checks passed on>
Done predicate: <the evidence, with the command output or screenshot path>
Screenshots: <paths>
Review fixes: <one line per defect or security finding fixed>
Out of scope: <problems seen outside this task, one line each, with file:line>
Decisions: <one line per non-obvious choice and its reason>
Blocker: <only for BLOCKED: what stopped you and what would unblock it>
```
