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

## 2026-02-20 — FID-001 Mechanics Matrix Lock (High-Impact TBD Removal)
**Decision:** Replace all high-impact `TBD` mechanics with explicit policy states in `docs/known_quirks.md`.

**Context:** Ambiguous `TBD` items were blocking fidelity work and making follow-up tickets underspecified.

**Options considered:**
1) Keep `TBD` placeholders until each mechanic is implemented
2) Lock policies now and adjust later if tests/sources prove gaps
3) Defer all decisions to milestone `M2`

**Outcome:** Option (2). The following policies are now locked:
- `1/256 miss glitch`: `Ignore`
- `Wrap/Fire Spin lock behavior`: `Approximate`
- `Hyper Beam recharge behavior`: `Approximate`
- `Focus Energy bug`: `Replicate`
- `Leech Seed + Toxic interaction`: `Ignore`

**Consequences / follow-ups:**
- `FID-010` owns exact partial trapping behavior.
- `FID-011` owns Hyper Beam recharge edge matrix.
- `FID-020` owns Toxic + Leech Seed interaction policy/implementation.

## 2026-02-20 — FID-002 Fidelity Source Grounding
**Decision:** Require each fidelity-critical mechanic to list at least one source reference and concrete implementation ownership (module/function).

**Context:** Mechanics policies existed without clear traceability to references or code, increasing regression and review risk.

**Options considered:**
1) Keep policy-only docs
2) Add source references only
3) Add source references plus implementation map

**Outcome:** Option (3). `docs/known_quirks.md` now includes:
- Source tags (`S1`, `S2`, `S3`) per mechanic
- Function-level implementation mapping for each policy row

**Consequences / follow-ups:**
- New mechanics tickets should update both policy and implementation mapping together.
- Reviews can now validate behavior against both source and owning code path.

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
