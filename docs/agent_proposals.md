# Agent Proposals for PokemonGen1

> Date: 2026-02-15
> Status: Draft — for review and refinement

---

## Current Agent Roster

| Agent | Role | Trigger |
|-------|------|---------|
| **TESTER** | Run tests, golden checks, determinism validation | Code changes, mechanics changes, RNG modifications |
| **SCRIBE** | Process docs/scribe_inbox.md into README, CHANGELOG, CLAUDE.md | After validated implementations, on request |
| **SCOUT** | Discover code locations, explore codebase | When files/symbols are unclear |

---

## Proposed Agents

### 1. BUILDER

**Purpose:** Automate build, run, and smoke-test workflows. Verify that the project runs end-to-end after changes — not just that tests pass, but that the actual interactive/batch flows work.

**Capabilities:**
- Run `python3 main.py` in a headless/automated mode and verify it doesn't crash
- Run `python3 scripts/batch_battle.py --battles 10 --format 3v3` and validate output
- Run `python3 scripts/validate_battle_log.py` against generated logs
- Verify new dependencies import correctly
- Check for import cycles after structural changes

**Trigger policy:**
- New files created
- Module structure changed (imports, __init__.py)
- Entry points modified (main.py, scripts/*)
- After TESTER passes — BUILDER is the "integration smoke test" layer

**Why it matters:**
Tests verify isolated units. BUILDER verifies the assembled system. Example: TESTER won't catch that `ui/menus.py` crashes on a small terminal size, but BUILDER's smoke run would.

**Tool access:** Bash, Read, Grep, Glob

---

### 2. MECH-CHECK — Gen 1 Mechanics Verifier

**Purpose:** Cross-reference engine implementation against canonical Gen 1 mechanics documentation. Catch inaccuracies that pass tests but produce wrong gameplay.

**Capabilities:**
- WebSearch/WebFetch against Bulbapedia, Smogon, and pret/pokered disassembly for authoritative formulas
- Compare implementation in `engine/damage.py`, `engine/status.py`, `engine/move_effects.py` against documented behavior
- Check edge cases: rounding direction, overflow behavior, 1/256 miss glitch, crit formula, badge boosts
- Produce a verification report: "Formula X in damage.py:42 matches/differs from source Y"
- Flag undocumented assumptions or deviations

**Trigger policy:**
- When `engine/battle.py`, `engine/damage.py`, `engine/status.py`, `engine/move_effects.py`, `engine/stat_modifiers.py` are modified
- When implementing a new move effect or status interaction
- On-demand: "verify [mechanic] is correct"

**Why it matters:**
The project's "hot spots" (CLAUDE.md) are all mechanics accuracy issues. Golden tests ensure *stability* (output doesn't change), but not *correctness* (output matches Gen 1). MECH-CHECK fills that gap.

**Reference sources (priority order):**
1. pret/pokered disassembly (ground truth)
2. Bulbapedia mechanics pages
3. Smogon damage calculator / research threads
4. Showdown source code (cross-reference)

**Tool access:** Read, Grep, Glob, WebSearch, WebFetch

---

### 3. AI-STRATEGIST — Battle AI Development Agent

**Purpose:** Design, implement, and evaluate AI strategies for computer-controlled players. Covers move selection, Pokemon switching, team building, and threat assessment.

**Capabilities:**
- Analyze battle logs to identify optimal decision patterns
- Implement new AI tiers (currently only `AIType.RANDOM` exists):
  - **SMART:** Type-aware move selection, switch on bad matchups
  - **COMPETITIVE:** Prediction, hazard awareness, status strategy
  - **ADAPTIVE:** Learns opponent patterns mid-battle
- Run batch simulations comparing AI tiers (win rates, average turns, move diversity)
- Evaluate team-building heuristics (type coverage, role balance, speed tiers)
- Suggest improvements based on common AI failure modes (e.g., never switches, wastes status moves)

**Trigger policy:**
- When implementing new AI types or modifying `get_random_ai_action()`
- When adding new move effects that AI should account for
- On-demand: "evaluate AI performance" or "design AI for [tier]"

**Why it matters:**
AI quality defines the player experience. Right now both sides use random moves — adding intelligence is a major milestone. This agent would own the full cycle: design strategy → implement → benchmark → iterate.

**Key files it would touch:**
- `engine/team_battle.py` (action selection functions)
- `settings/battle_config.py` (AIType enum expansion)
- New: `engine/ai/` module (strategy implementations)
- `scripts/batch_battle.py` (comparative benchmarks)

**Tool access:** Bash, Read, Write, Edit, Grep, Glob

**Design considerations:**
- AI should be pure functions: `(game_state) -> action` — no side effects
- AI should respect clauses (Sleep Clause, OHKO Clause, etc.)
- AI decisions should be deterministic when seeded (use `get_rng()`)
- Different AI levels should be testable in isolation (unit tests, not just batch)

---

### 4. UI-ARCHITECT — User Interface Specialist

**Purpose:** Design and implement curses-based (and eventually graphical) UI components. Owns the visual layer, layout system, and interaction patterns.

**Capabilities:**
- Design new curses screens following established patterns (init_colors, draw_*, select_*_curses)
- Handle terminal size constraints gracefully (safe_addstr, responsive layouts)
- Implement animation and transition effects for battle events
- Prototype new UI concepts (team preview, move tooltips, battle replay)
- Ensure consistent color theming and navigation patterns across all screens
- Eventually: migrate from curses to a graphical framework (pygame, textual, etc.)

**Trigger policy:**
- When implementing new screens or modifying existing UI
- When adding features that need visual representation
- On-demand: "design UI for [feature]"

**Why it matters:**
The UI is growing in complexity (we just added menus, config forms, battle log panels). A dedicated agent ensures consistency and prevents the UI code from becoming a tangle of raw curses calls. It would also own the eventual migration to a richer UI framework.

**Key files it would own:**
- `ui/menus.py` (navigation flow)
- `ui/selection.py` (curses widgets)
- `engine/display.py` (ANSI display utilities)
- New: `ui/components.py` (reusable UI primitives — if complexity warrants it)

**Tool access:** Read, Write, Edit, Grep, Glob, Bash (for terminal testing)

**Design considerations:**
- All UI code must handle small terminals (min 80x24) without crashing
- Color pairs are a shared resource — maintain a registry to avoid conflicts
- Navigation must be consistent: ESC=back, ENTER=confirm, arrows=navigate
- UI must never block engine logic — clean separation via callbacks

---

## Agent Interaction Map

```
User Request
    │
    ├─► SCOUT (discovery)
    │       │
    ├─► [implement changes]
    │       │
    ├─► MECH-CHECK (if mechanics touched)
    │       │
    ├─► TESTER (unit + golden)
    │       │
    ├─► BUILDER (integration smoke test)
    │       │
    ├─► SCRIBE (documentation)
    │       │
    └─► done

Special workflows:
    AI work ──► AI-STRATEGIST ──► TESTER ──► BUILDER (batch benchmarks)
    UI work ──► UI-ARCHITECT ──► TESTER ──► BUILDER (smoke test)
```

---

## Priority Order for Implementation

| Priority | Agent | Rationale |
|----------|-------|-----------|
| 1 | **MECH-CHECK** | Correctness is the project's core value prop; hot spots are a known risk |
| 2 | **BUILDER** | Bridges the gap between "tests pass" and "it actually works" |
| 3 | **AI-STRATEGIST** | Unlocks the next major feature milestone (smart AI) |
| 4 | **UI-ARCHITECT** | Becomes critical as UI complexity grows; less urgent today |

---

## Open Questions

- Should MECH-CHECK produce persistent verification reports (e.g., `docs/mechanics_audit.md`)?
- Should AI-STRATEGIST own its own benchmark data directory (e.g., `data/ai_benchmarks/`)?
- When should UI-ARCHITECT be activated — after curses UI is "done" and we migrate, or now?
- Should BUILDER be merged with TESTER, or kept separate for clearer responsibilities?
- What's the minimum AI tier to implement first? (Suggestion: SMART — type-aware move selection)
