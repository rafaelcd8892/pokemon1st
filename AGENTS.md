# Agent Working Agreement (Pokémon Gen 1 Battle Engine)

## Project goal
Build a deterministic Pokémon Gen 1 battle engine (core mechanics first), with a stable battle log output and regression tests.

## Golden rule
**Do not change the battle log format** unless the ticket explicitly says so.

## How to work (every ticket)
1. Read `docs/agent_brief.md` and `docs/known_quirks.md`.
2. Propose a short plan (max 8 bullets) + list of files you will touch.
3. Implement with the smallest possible diff.
4. Add/adjust tests.
5. Run validation commands and report results.

## Scope control
- Touch only the files listed in the ticket.
- If more files are needed, stop and explain why.
- Avoid large refactors unless requested.

## Directories agents must ignore
- logs/
- __pycache__/
- .pytest_cache/
- venv/
- any generated files

## Definition of Done (DoD)
- [ ] Tests added/updated
- [ ] `pytest -q` (or project test command) passes
- [ ] Golden logs unchanged (unless ticket says otherwise)
- [ ] Deterministic output with fixed seed
- [ ] Summary of changes + how to verify

## Output format expected from agents
- Plan (bullets)
- Files changed (bullets)
- Commands run (copy/paste)
- Notable risks / edge cases (bullets)

## Style / conventions
- Prefer small pure functions for mechanics (damage, accuracy, crit, status).
- Keep I/O and formatting isolated from battle mechanics.
- Avoid “clever” abstractions; favor readability and testability.