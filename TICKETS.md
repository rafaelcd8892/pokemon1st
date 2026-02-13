# Agent Tickets Template

## Ticket title
<short imperative title>

## Goal
What should be implemented or changed.

## Constraints
- Files allowed:
  - `...`
- Must NOT change:
  - battle log format
  - public API: `...`
- Determinism: seed must produce identical results

## Acceptance criteria
- [ ] Unit tests added
- [ ] Golden logs unchanged (or updated with approval)
- [ ] `pytest -q` passes

## Validation
Commands to run:
- `pytest -q`
- `python scripts/run_golden.py`

## Notes
Edge cases to consider:
- ...