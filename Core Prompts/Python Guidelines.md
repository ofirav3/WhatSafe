## Python code guidelines

### Naming
- Use descriptive, full-word names. Avoid 1–2 letter names.
- Functions: verbs/verb-phrases. Variables: nouns/noun-phrases.
- Constants UPPER_SNAKE_CASE; modules/files lower_snake_case; classes PascalCase.

### Types and interfaces
- Add type hints for function signatures and public APIs.
- Avoid `Any` unless necessary; prefer precise types.
- Use `@dataclass` for simple data containers.

### Structure and readability
- Favor small, single-responsibility functions.
- Use guard clauses and early returns over deep nesting.
- Keep modules cohesive; avoid cyclic imports.

### Errors and logging
- Don’t blanket-catch exceptions; catch the narrowest exception.
- Log meaningful context; don’t swallow errors silently.
- Convert internal errors to user-friendly messages at API boundaries.

### Control flow
- Avoid unnecessary try/except blocks.
- Prefer explicit over implicit behavior; be clear about return values.

### Comments
- Only add comments for non-obvious rationale, invariants, and caveats.
- Don’t restate what the code already makes obvious.

### Formatting
- Follow PEP 8; keep lines reasonably short.
- Consistent indentation and whitespace; no unrelated reformatting.

### Testing and validation
- Validate external inputs at module boundaries (e.g., HTTP, CLI).
- Keep pure logic testable and free of side effects.

### Dependencies
- Pin or bound versions when interoperability matters.
- Keep runtime deps minimal; prefer stdlib where feasible.

### Performance and safety
- Avoid premature optimization; measure before tuning.
- Be careful with regexes and large inputs; validate size and timeouts.


