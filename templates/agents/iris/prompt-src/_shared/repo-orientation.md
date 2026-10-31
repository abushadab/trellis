Start from `{{config:repo_root}}`. Discover the parts relevant to the assignment instead of assuming a fixed map of subsystems.

Useful starting docs, when they exist: the top-level `README.md` and the architecture, platform, operations, and testing docs.
{{if:runtime_guide}}
`{{config:runtime_guide}}` says how to run, test, and seed the application locally. Use it as the selected runtime boundary and never infer a different target from what happens to be running.
{{/if}}

Many test and scenario scripts need a configured runtime: environment variables, containers, services, network, writable folders, or test databases. Read them rather than run them. Run a scenario script only when the assignment explicitly allows it and it is safe.
