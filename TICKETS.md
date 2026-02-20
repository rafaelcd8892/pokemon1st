# Pokemon Gen 1 Roadmap Tickets (Fidelity First)

## Global Rules
- Do not change battle log format unless the ticket explicitly allows it.
- Determinism is mandatory: fixed seed must produce identical outcomes.
- Prefer minimal diffs and isolated mechanics changes.
- Every mechanics change must include tests.

## Milestones
- M1 Stability: spec lock + highest-impact mechanics parity.
- M2 Coverage: edge-case quirks + scenario depth.
- M3 Enforcement: CI fidelity gates and regression hardening.

---

## FID-001 Mechanics Matrix Lock
Status: `Backlog`

Goal:
- Replace high-impact `TBD` items in `docs/known_quirks.md` with explicit policy:
  - `Replicate`, `Approximate`, or `Ignore`.

Files allowed:
- `docs/known_quirks.md`
- `docs/decisions.md`

Acceptance criteria:
- [ ] No high-impact mechanic remains `TBD` (or explicitly deferred with reason/date).
- [ ] Each decision has a short rationale.
- [ ] `docs/decisions.md` has matching entries.

Validation:
- `pytest -q`

---

## FID-002 Mechanics Source Grounding
Status: `Backlog`

Goal:
- Add source references for fidelity-critical mechanics and where they are implemented.

Files allowed:
- `docs/known_quirks.md`
- `docs/agent_brief.md`
- `docs/decisions.md`

Acceptance criteria:
- [ ] Each fidelity-critical mechanic has at least one source reference.
- [ ] Each mechanic maps to implementation modules/functions.

Validation:
- `pytest -q`

---

## FID-003 Mechanics Ticket Checklist Template
Status: `Backlog`

Goal:
- Add a reusable ticket/checklist section for future mechanics work:
  - decision note
  - unit test
  - integration test
  - golden verification

Files allowed:
- `AGENTS.md`
- `docs/agent_brief.md`

Acceptance criteria:
- [ ] Checklist exists in docs and is easy to copy into tickets.
- [ ] Checklist includes explicit “no log format change” guard.

Validation:
- `pytest -q`

---

## FID-010 Partial Trapping Exact Behavior
Status: `Backlog`
Priority: `P1`

Goal:
- Implement Gen 1-consistent behavior for Wrap/Bind/Clamp/Fire Spin lock and turn interactions.

Files allowed:
- `engine/battle.py`
- `engine/move_effects.py`
- `models/pokemon.py`
- `tests/test_gen1_mechanics.py`
- `tests/test_battle_integration_regressions.py`
- `tests/scenarios/*.json` (if needed)
- `tests/golden/*.json` (only if explicitly approved)

Acceptance criteria:
- [ ] Trap duration and lock behavior match chosen policy from `FID-001`.
- [ ] Relevant edge cases are covered by unit/integration tests.
- [ ] Golden logs unchanged unless approved.

Validation:
- `pytest -q`
- `python3 scripts/run_golden.py`

---

## FID-011 Hyper Beam Recharge Edge Cases
Status: `Backlog`
Priority: `P1`

Goal:
- Confirm and implement exact recharge rules for KO and edge interactions.

Files allowed:
- `engine/battle.py`
- `engine/move_effects.py`
- `tests/test_gen1_mechanics.py`
- `tests/test_battle_integration_regressions.py`

Acceptance criteria:
- [ ] Recharge behavior matches locked policy.
- [ ] KO/non-KO branch behavior covered by tests.
- [ ] No deterministic regressions.

Validation:
- `pytest -q`
- `python3 scripts/run_golden.py`

---

## FID-012 Focus Energy Bug Parity Lock
Status: `Backlog`
Priority: `P1`

Goal:
- Verify full Focus Energy bug parity and prevent future drift.

Files allowed:
- `engine/damage.py`
- `tests/test_damage.py`
- `tests/test_gen1_mechanics.py`

Acceptance criteria:
- [ ] Crit-rate behavior matches documented Gen 1 bug policy.
- [ ] Tests pin expected probabilities/branch behavior.

Validation:
- `pytest -q`

---

## FID-013 Sleep/Freeze Clause Policy Parity
Status: `Backlog`
Priority: `P1`

Goal:
- Ensure battle clauses align with Stadium policy and project decisions.

Files allowed:
- `engine/clauses.py`
- `engine/battle.py`
- `engine/status.py`
- `tests/test_clauses.py`
- `tests/test_gen1_mechanics.py`

Acceptance criteria:
- [ ] Sleep/Freeze clause interactions match documented policy.
- [ ] Self-induced and move-induced states are correctly distinguished where required.

Validation:
- `pytest -q`

---

## FID-020 Toxic + Leech Seed Interaction
Status: `Backlog`
Priority: `P2`

Goal:
- Decide and implement Toxic counter interaction with residual effects.

Files allowed:
- `engine/status.py`
- `engine/battle.py`
- `engine/move_effects.py`
- `docs/known_quirks.md`
- `docs/decisions.md`
- `tests/test_gen1_mechanics.py`

Acceptance criteria:
- [ ] Behavior is documented and implemented consistently.
- [ ] Residual ordering and damage scaling are tested.

Validation:
- `pytest -q`
- `python3 scripts/run_golden.py`

---

## FID-021 Accuracy/Evasion and 1/256 Policy
Status: `Backlog`
Priority: `P2`

Goal:
- Finalize policy and implement/test either replication or explicit non-replication of 1/256 behavior.

Files allowed:
- `engine/battle.py`
- `engine/stat_modifiers.py`
- `config.py`
- `docs/known_quirks.md`
- `tests/test_gen1_mechanics.py`

Acceptance criteria:
- [ ] Accuracy/evasion behavior and 1/256 policy are explicit and test-covered.
- [ ] No ambiguous TBDs remain for this mechanic.

Validation:
- `pytest -q`

---

## FID-022 Freeze Thaw/Cure Edge Rules
Status: `Backlog`
Priority: `P2`

Goal:
- Lock and verify freeze cure behavior across fire-hit and special cases.

Files allowed:
- `engine/status.py`
- `engine/battle.py`
- `tests/test_gen1_mechanics.py`

Acceptance criteria:
- [ ] Freeze persistence/cure logic matches policy.
- [ ] Interactions with status precedence are tested.

Validation:
- `pytest -q`

---

## FID-023 Bide Exact Behavior
Status: `Backlog`
Priority: `P2`

Goal:
- Implement Gen 1-consistent Bide behavior (lock turns, damage storage, and release resolution).

Files allowed:
- `engine/battle.py`
- `engine/move_effects.py`
- `models/pokemon.py`
- `tests/test_gen1_mechanics.py`
- `tests/test_battle_integration_regressions.py`
- `tests/scenarios/*.json` (if needed)
- `tests/golden/*.json` (only if explicitly approved)

Acceptance criteria:
- [ ] Bide no longer resolves as a normal power-0 attack.
- [ ] Turn lock and retaliation behavior are covered with unit/integration tests.
- [ ] Deterministic behavior is preserved with fixed seed.
- [ ] Golden logs unchanged unless explicitly approved.

Validation:
- `pytest -q`
- `python3 scripts/run_golden.py`

---

## FID-030 Canonical Fidelity Scenario Suite
Status: `Backlog`
Priority: `P2`

Goal:
- Add deterministic scenarios for each high-risk mechanic to guard against regressions.

Files allowed:
- `tests/scenarios/*.json`
- `tests/test_golden.py`
- `tests/golden/*.json` (with explicit approval)
- `tests/README.md`

Acceptance criteria:
- [ ] Scenario set covers all P1 mechanics.
- [ ] Scenarios are seed-pinned and reproducible.

Validation:
- `pytest -q tests/test_golden.py`
- `python3 scripts/run_golden.py`

---

## FID-031 Per-Mechanic Regression Tags
Status: `Backlog`
Priority: `P3`

Goal:
- Improve test discoverability by grouping/marking mechanics-focused regressions.

Files allowed:
- `tests/*`
- `tests/README.md`
- `pytest.ini` (if introduced)

Acceptance criteria:
- [ ] Tests can be filtered by mechanic or marker.
- [ ] Documentation includes marker usage.

Validation:
- `pytest -q`

---

## FID-032 Fidelity CI Gate
Status: `Backlog`
Priority: `P3`

Goal:
- Enforce fidelity checks in CI: unit + integration + golden + optional batch smoke.

Files allowed:
- CI config files (when added)
- `scripts/run_golden.py`
- `scripts/batch_battle.py`
- `README.md`

Acceptance criteria:
- [ ] CI fails on golden mismatch or deterministic regression.
- [ ] CI steps are documented for local replication.

Validation:
- `pytest -q`
- `python3 scripts/run_golden.py`
- `python3 scripts/batch_battle.py --battles 20 --format 3v3 --seed 42`

---

## FID-033 Moveset Quality Scoring + Bide Overuse Control
Status: `Backlog`
Priority: `P2`

Goal:
- Define a reproducible way to score/compare generated movesets and reduce pathological move selection (notably `Bide` overuse).
- Ensure random/smart-random movesets remain diverse and competitive without repeatedly selecting low-value filler moves.

Files allowed:
- `data/data_loader.py`
- `tests/test_moveset_selection.py`
- `scripts/batch_battle.py`
- `tests/test_battle_integration_regressions.py` (if needed)
- `docs/agent_brief.md` (if metric/reporting notes are added)

Acceptance criteria:
- [ ] A deterministic moveset-quality signal is defined (at minimum: role coverage + damaging/status balance + STAB utility).
- [ ] Baseline measurement for generated movesets is documented (including `Bide` pick rate under fixed seed).
- [ ] Selection logic reduces `Bide` overuse in random/smart-random generation while preserving variety.
- [ ] Tests pin the anti-overuse behavior and prevent regressions.

Validation:
- `pytest -q tests/test_moveset_selection.py`
- `pytest -q tests/test_battle_integration_regressions.py`
- `python3 scripts/batch_battle.py --battles 100 --format 3v3 --moveset smart_random --seed 42`

---

## Suggested Execution Order
1. `FID-001`
2. `FID-002`
3. `FID-003`
4. `FID-010`
5. `FID-011`
6. `FID-012`
7. `FID-013`
8. `FID-020`
9. `FID-021`
10. `FID-022`
11. `FID-023`
12. `FID-033`
13. `FID-030`
14. `FID-031`
15. `FID-032`
