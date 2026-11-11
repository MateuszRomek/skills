# Slicing a specification

Read this when the program's input is a specification or a multi-phase plan instead of a list of issues. The result is the task list for `program.py init`.

## Acceptance matrix

Read the specification, the repository instructions, relevant ADRs, the domain glossary, the current implementation, its call sites, tests, and public contracts. Map every requirement or user story to:

- the owning module or boundary;
- the observable result;
- the verification seam, which becomes the task's done predicate;
- the task that will implement it.

The matrix is complete when every in-scope requirement has one task and one observable proof, and every out-of-scope item stays excluded. Write it into `program.md`. A multi-phase plan already carries this: each PR section is one task, and its evidence boxes are the done predicate.

## Cut the tasks

Each task has one coherent behavior, invariant, or structural outcome, explicit dependencies, a bounded write area, a checkable done predicate, and a risk level. Take the smallest task that stays useful and verifiable on its own. Cut by what a reviewer needs to hold in their head, never by file count or line limit.

Classify every relationship:

- **Independent.** Starts from main and becomes its own PR.
- **Dependent.** Needs an earlier task. It waits for that task's merge or stacks on it per [`stacks.md`](stacks.md).
- **Absorbed.** Too small to verify on its own. Fold it into its owning task.

An edge belongs in the graph only when it is a real implementation dependency, never a preferred reading order.

## Design gates

- A task that introduces or changes a boundary, data model, public contract, or module ownership gets the **architect** skill in its worker brief.
- Two or more viable designs that no prototype has settled go through the **arena** skill before the task starts.
- Contested architecture goes through the **interrogate** skill before dispatch.
- A security-sensitive task (authentication, authorization, credentials, cryptography, personal data, destructive migrations, external input, permission boundaries) gets an abuse case and a negative test in its done predicate, and the `security` verification level.
- A product or architecture decision the specification leaves open goes back to the user before its task starts.
