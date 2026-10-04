# Known Quirks — Gen 1 Mechanics Policy

This document defines which Gen 1 quirks we **replicate**, **approximate**, or **ignore**.
Agents must follow this policy. If a ticket requires changing it, update this document and add a decision entry.

## Status: choose one per item
- ✅ Replicate
- ⚠️ Approximate
- ❌ Ignore

## Rounding / integer behavior
- Damage rounding rules: ⚠️ Approximate (document exact formula in code + tests)
- Stat modifiers rounding: ⚠️ Approximate

## Critical hits
- Crit rate based on Speed: ✅ Replicate
- High-crit moves behavior: ✅ Replicate

## Turn order / move priority
- Move priority: ✅ Replicate (decided 2026-10-03)
  - Order each turn: switches first, then attacks by priority (higher first), then modified Speed (stat stages + paralysis ÷4), then a random coin flip on a tie.
  - Gen 1 priorities: Quick Attack +1, Counter −1, every other move 0. Source: `priority` in data/moves.json.
  - The priority used is that of the move that will actually execute this turn: a charging move's second turn, a Thrash/Petal Dance lock, or the move chosen this turn.
  - 0 priority when no move executes: recharging (Hyper Beam), trapped by Wrap/Bind, or using Struggle.
  - Metronome and Mirror Move use their own priority (0). The called move's priority is ignored (a Metronome-called Quick Attack does not go first).
  - Log: when priority decides the order, `turn_order` uses reason `"priority"` instead of `"speed"`. Existing reasons and wording are unchanged.

## Accuracy quirks
- 1/256 miss glitch: ❓ TBD (default: ❌ Ignore)
- Accuracy/evasion stage behavior: ⚠️ Approximate (needs tests)

## Freeze
- Freeze permanence in Gen 1 (only thaw by specific moves): ✅ Replicate (if implemented)
- Freeze overriding other statuses: ⚠️ Approximate

## Partial trapping / multi-turn
- Wrap/Fire Spin lock behavior: ❓ TBD
- Recharge (Hyper Beam) in Gen 1: ❓ TBD

## Misc
- Focus Energy bug: ❓ TBD
- Leech Seed + Toxic interactions: ❓ TBD

## Notes
If an item is TBD, agents must:
1) implement nothing beyond current behavior, or
2) propose a plan + add a decision before changing behavior.