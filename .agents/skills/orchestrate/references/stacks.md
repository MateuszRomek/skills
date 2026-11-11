# Stacked tasks

Read this when `program.py ready` prints a `can-stack:` or `restack:` line.

## When to stack

Waiting for the parent's merge is the default. Stack a dependent task on its parent's open PR only when all of these hold:

- a worker slot is free and no unstacked task is ready to fill it;
- the parent is in `verifying` or `merging`, so its PR and head exist;
- every other dependency of the task has merged.

`program.py` enforces the last two. Start the stacked worker with `program.py set <program-dir> <task> --status building base=<parent>`. Its brief names the parent's branch as the starting point and the PR base, and pastes the parent's report in full.

## Open the stacked PR

Detect the native path before changing Git state:

```sh
gh --version
gh stack --help
```

Use GitHub's native stacks only when `gh stack --help` succeeds. They need GitHub CLI 2.90.0 or later and the `github/gh-stack` extension, and the feature is in public preview. Installing or upgrading tools, adding the extension, or enabling the preview needs the user's explicit request. References: <https://docs.github.com/en/pull-requests/reference/stacked-pull-requests> and <https://github.com/github/gh-stack>.

- **Native path.** The worker opens its PR through **prepare-pull-request** with the parent branch as base, then registers it with the `gh stack link` form the installed CLI shows, and reads it back with `gh stack view`. Use **prepare-pull-request** for every layer, so the repository's PR body and readiness checks still run.
- **Manual path.** The worker opens an ordinary PR through **prepare-pull-request** whose base is the parent branch, and verifies the base and head after publication.

## Merge and restack

The merge order is always bottom-up. `program.py` refuses `merging` for a task whose dependencies have not merged.

After the parent merges, `program.py ready` prints `restack:` for its child. Send a fresh worker to move the child onto main. With squash merges the child branch still carries the parent's original commits, so it rebases with `git rebase --onto main <parent's last pushed SHA>`. It then retargets the PR base to main, pushes with `--force-with-lease` pinned to the child's last head, and gets checks green. Record the new head, run `program.py set <program-dir> <task> base=main`, and rerun the lanes the fix-round rule in [`verification.md`](verification.md) names.
