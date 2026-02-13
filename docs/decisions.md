# Engineering Decisions Log

Use this file to record decisions that affect behavior, architecture, or test strategy.
Format:
- Date (YYYY-MM-DD)
- Decision
- Context
- Options considered
- Outcome
- Consequences / follow-ups

---

## 2026-02-13 — Example Decision: Deterministic RNG interface
**Decision:** All randomness must be sourced from a single RNG object passed through battle context.

**Context:** Multiple modules were using `random` directly, causing nondeterminism in tests.

**Options considered:**
1) Global seed on import
2) Pass RNG via battle context (preferred)
3) Wrap RNG calls behind `rng.py` module

**Outcome:** Option (2) with a small `RNG` wrapper.

**Consequences / follow-ups:**
- Update modules to accept `rng` dependency
- Add a regression test verifying determinism