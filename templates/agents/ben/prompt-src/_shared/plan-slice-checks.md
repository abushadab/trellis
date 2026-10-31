For each component boundary that decides the outcome, compare what the real producer supplies (existing or planned) with what its consumer needs: state, credentials, or capability.

- Base the comparison on the real code and configuration. Inspecting each component on its own is not enough.
- Include prerequisites that tests seed by hand instead of getting them from the producer.
- Each mismatch needs an owner and a dependency order before the plan is ready.

For the active slice, also check these:

- **Durable steps:** when the slice adds saved phases, markers, or intents, the plan has a `Durable steps` section. For each step it says what resumes it, what ends it when the outcome is definite, what it releases, and how it behaves on a definite failure versus an ambiguous one. Holding resources while effects are uncertain is fine, and some holds rightly outlive the operation. The section is left out when the slice adds no durable state.
- **Safeguards:** for each safeguard the slice adds, the plan names the existing valid flows it could disrupt and plans one positive check for each flow.
- **Caller inputs:** the plan lists each new or changed caller-visible input (query key, header, path segment, or body field). The source must settle how each one is read, and it must not collide with names that existing requests already pass through. If the source does not settle it, the plan must route it as a blocker.
