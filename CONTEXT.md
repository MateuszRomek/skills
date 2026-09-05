# Context

## Agent mode routing

- **Semantic work unit.** A bounded piece of task content with a result contract. It does not select a model or imply a worker count.
- **Role.** A stable name that connects semantic work to one host-local route.
- **Routing profile.** The machine-local, user-confirmed Agent mode configuration for one host. It is the only persistent owner of delegation mode, limits, worker rosters, models, reasoning efforts, and inheritance.
- **Worker roster.** The complete ordered set of assignments available to one role invocation. Its length is configured capacity, not a concurrency value.
- **Task worker limit.** The maximum total subagent starts across one top-level task, including retries and nested Agent mode workflows.
- **Concurrency limit.** The maximum number of subagents active at the same time in one top-level task.
- **Delegation depth.** The deepest configured child level. The root is depth 0, so depth 1 allows root-owned children and no grandchildren.
- **Delegation reservation.** Start and concurrency credits removed from a parent's remaining budget and assigned exclusively to one child's subtree. The child returns unused credits when it completes.
- **Coordinator execution.** The route keeps work in the root task and starts no subagent.
- **Partition dispatch.** Distinct semantic work units are distributed across no more than the configured roster and remaining task-start budget. Fewer units may use fewer workers; extra units reuse the resolved workers.
- **Replicate dispatch.** The same brief is sent to the complete configured roster. The workflow does not silently shrink or expand it.
