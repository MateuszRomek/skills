Agent mode is installed. Invoke the `agent-mode` skill and follow it when a task meets any of these:

- it touches more than one file, or changes a signature other files call
- it involves a design or architecture choice
- it is a bug whose cause is not yet known, or a performance issue

Route each new task this way. An earlier invocation in this session does not cover a new task.

For smaller tasks, such as a contained change to one file, a question, or a one-line edit, work directly and verify on the real artifact. When the request already names a narrower skill, such as `how`, `why`, `architect`, `arena`, `interrogate`, or `tdd`, enter it directly.

User instructions in CLAUDE.md, AGENTS.md, or the conversation take precedence.
