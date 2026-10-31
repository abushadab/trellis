A slice should let one Implementation Engineer complete a coherent change and one Implementation Reviewer check it fully.

Keep connected implementation, fixtures, and focused tests together when they can be built and checked safely as one task. Touching several services, covering several ACs, or preparing a disposable runtime does not by itself require a split.

Split when a concrete dependency, separate authority decision, or amount of work would prevent reliable implementation or review in one task. Name that reason and what each smaller slice can prove on its own. Keep the order safe and assign final integration to an owner.

Destructive fixtures still need clear ownership, target checks, and cleanup. Give them a separate slice only when that resolves a concrete safety or dependency problem.

Do not split by file, mechanical step, or test ownership. Do not add scaffolding only to create a boundary. Write the work plainly; wording or length alone does not decide its size.
