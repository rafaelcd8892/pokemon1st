# Battle Audit Contract

## Purpose
Define a minimal, enforceable logging contract so battle outcomes are reproducible and anomalies are detectable automatically.

## Canonical Source
- Canonical artifact: `logs/battles/<battle_id>.json`
- Human-readable `.log` is a rendering view and may omit structured fields.

## Core Rule
`No state change without a causal event.`

Any HP/status/switch/faint change must be traceable to one or more explicit events in the same turn.

## Required Event Types
- `turn_start`
- `move`
- `miss`
- `effect`
- `status`
- `switch`
- `hp`
- `faint`
- `turn_end`

## Required Fields Per Entry
Every entry must include:
- `turn`
- `action_type`
- `pokemon`
- `details` (object)
- `message` (optional string)

For `move` events, `details` must include:
- `move`
- `damage`
- `effectiveness`
- `critical`
- `result` (`resolved`, `charge_start`, `blocked_by_invulnerability`, etc.)

For `hp` events, `details` must include:
- `current_hp`
- `max_hp`

## Audit Invariants
1. Turn boundaries
- Every non-zero turn should include `turn_start` and `turn_end`.

2. Faint causality
- If `faint` occurs on turn T for Pokemon X, at least one causal event in turn T must explain HP reaching 0:
  - `move` targeting X with `damage > 0`, or
  - `effect` on X with `damage > 0`, or
  - `move` from X with `self_faint == true` (e.g. `Explosion`/`Self Destruct`), or
  - an `hp` event for X with `current_hp == 0` plus causal event in same turn.

3. Switch validity
- A `switch` event for incoming Pokemon Y must not be immediately followed by an `hp` snapshot with `current_hp <= 0` in the same turn.

4. Self-target semantics
- Known self-target non-damaging moves must target the actor itself in logs:
  - `Agility`, `Barrier`, `Amnesia`, `Reflect`, `Light Screen`, `Recover`, `Rest`, `Soft Boiled`, `Substitute`, `Swords Dance`, `Withdraw`, `Harden`, `Growth`, `Meditate`, `Minimize`.

5. HP consistency
- `hp.current_hp` must satisfy `0 <= current_hp <= max_hp`.

## Severity Levels
- `ERROR`: contract violation that breaks replay/audit reliability.
- `WARN`: suspicious but potentially legal sequence.

## Validation Tool
Use:

```bash
python3 scripts/validate_battle_log.py logs/battles/<file>.json
```

Exit code:
- `0`: no `ERROR`
- `1`: at least one `ERROR`

## CI Recommendation
Include validator checks in tests for representative battles and synthetic edge cases.
