{{if:serena}}
Use Serena's MCP tools for code semantics in `{{config:repo_root}}`. One shared Serena serves every agent and is set to that directory. It cannot read any other worktree.

- Use `get_symbols_overview` before reading unfamiliar whole source files.
- Use `find_symbol` for any named code symbol.
- Use `find_referencing_symbols` before concluding anything about a symbol that may have callers.

Use `rg` through Bash, or a targeted Read, for exact strings and non-code artifacts: routes, environment or config keys, migrations, SQL, scripts, tests, docs, and copy. Use shell only for short, predictable, non-mutating checks and small inventories.
{{else}}
Use `rg` through Bash and targeted Reads for code and for exact strings: routes, environment or config keys, migrations, SQL, scripts, tests, docs, and copy. Search for a named symbol's definition before reading unfamiliar whole source files. Search for its references before concluding anything about a symbol that may have callers. Use shell only for short, predictable, non-mutating checks and small inventories.
{{/if}}
