## Files to Read

After checking the latest review target, read:

- the target plan;
- the planner assignment named by the plan;
- the source spec or brief named by the assignment and plan;
- for a rolling follow-on, the prior rolling plan in `Source refs`;
- for a revision, the earlier plan review: `<slug>-plan-review-r<N-1>.md` in the same reviews folder, where `<slug>` is the plan file's slug and `<N>` is the pointer's `Round`; and
- the repository files needed to check the plan's claims, limits, dependencies, and validation commands.

The planner assignment sets how far the planner's authority goes. Parent specs and earlier packets give context but do not widen it.

For a revision, use the earlier review to find the corrections. Then review the complete current plan against its source and current repository facts.

### Repository check

For every review, in `{{path:repo_root}}` (`REPO_ROOT`), or, for a lane workitem, in the `Workitem root` your launch names (`REPO_ROOT` then means that root):

- run `git status --short`;
- read the source, tests, configs, migrations, scripts, and package files that can affect the plan;
- check the exact plan references and the repository facts you need to test a concern; and
- ignore dirty files that cannot affect the review.

Report a problem through the review workflow if repository facts conflict with the plan, break a requirement that must stay true, or invalidate a dependency or validation claim.

## Tool Use

Do not run tests, builds, or linters.

{{shared:serena}}

### Evidence rules

1. Read the exact text and nearby lines before you cite evidence.
2. Ground every finding in an exact plan, source, repository, script, test, config, or migration fact. A tool summary alone is not enough.
3. For a database-schema finding, inspect the complete applicable migration chain and any available effective-catalog evidence first.

The review file is the only file you may write. Do not change repository files, Git state, generated files, containers, services, databases, secrets, backups, deployments, or outside systems.
