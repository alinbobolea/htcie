1. Update code docstrings and documentation.


Documentation enhancement

You are a senior Python engineer and technical writer.

Your task is to review and enhance documentation across the following project:

- /home/nick/projects/htcie/src
- /home/nick/projects/htcie/tests
- /home/nick/projects/htcie/notebooks

Follow ALL rules defined in CLAUDE.md. Do not restate or override them.

---

## Objectives

1. Add missing docstrings across the codebase.
2. Improve clarity, depth, and accuracy of existing docstrings.
3. Expand high-level project documentation.
4. Ensure documentation reflects actual behavior and usage.

---

## Scope Clarification

The following are ALREADY enforced by CLAUDE.md and must NOT be redefined:
- Type hints and typing rules
- Formatting (black, ruff)
- Linting and style conventions
- Testing framework and practices
- General coding philosophy

Focus ONLY on documentation quality, completeness, and accuracy.

---

## Docstring Expansion

### Apply where missing or weak:

- Internal functions (not just public APIs)
- Classes and methods
- Test functions (clarify intent, not mechanics)

### Requirements

- Use Google-style docstrings
- Emphasize:
  - Purpose and behavior (not implementation)
  - Input/output meaning (not just types)
  - Edge cases and constraints
  - Non-obvious logic
- Add examples ONLY where they improve understanding

### Avoid

- Repeating type hints already in the signature
- Generic phrases like “helper function”
- Overly verbose or redundant descriptions

---

## Code Understanding Process

Before modifying docstrings:

1. Infer module responsibilities and boundaries
2. Use `/tests` to understand intended behavior and edge cases
3. Use `/notebooks` to understand real-world workflows and usage patterns

Docstrings must reflect actual behavior—not assumptions.

---

## Module-Level Documentation

Ensure each module has a meaningful top-level docstring including:

- Purpose of the module
- Key responsibilities
- How it fits into the broader system

Avoid boilerplate descriptions.

---

## Project Documentation

### README.md

Enhance or create with:

- Clear project purpose
- High-level architecture overview
- Key workflows (derived from notebooks)
- How components interact (not setup instructions unless missing)

### /docs (if missing or incomplete)

Create or improve:

- Architecture.md
  - Major components and relationships
  - Data flow between modules

- API.md
  - Public-facing interfaces
  - Expected usage patterns

- Workflows.md
  - End-to-end usage flows
  - Derived from notebooks

---

## Notebooks

Improve readability and structure:

- Add markdown cells explaining:
  - Purpose of the notebook
  - Each major step
  - Key outputs and conclusions
- Convert exploratory code into guided, readable workflows where possible

---

## Tests

Add docstrings that explain:

- What behavior is being validated
- Why the test exists (edge case, regression, contract)

Do NOT restate the test code.

---

## Constraints

- Do NOT modify business logic
- Do NOT refactor unless required for clarity of documentation
- Keep changes minimal and localized
- Do NOT introduce new dependencies

---

## Output Requirements

1. Apply changes directly to files
2. Ensure documentation is consistent across modules
3. Provide a final summary including:
   - Files updated
   - Types of improvements made
   - Any ambiguous or unclear areas in the codebase

---

## Optional (High-Value Only)

If clearly beneficial:

- Identify undocumented edge cases
- Highlight unclear or confusing logic (without rewriting it)

---

Work methodically. Prefer accuracy and clarity over completeness if tradeoffs arise.