Navigate the product repository (`{{path:repo_root}}`) with Read and scoped `rg` or `find` searches through Bash.

- Unfamiliar source file: Read its top-level structure (headings, declarations) before broad reading.
- Known symbol: `rg` for its definition, then Read only the part that matters.
- Shared symbol: `rg` for its callers and users with the most specific name, before concluding its impact.
- Exact text, config keys, routes, SQL, migrations, scripts, tests, docs, non-code files, or an unknown location: a scoped `rg` or `find` search.
