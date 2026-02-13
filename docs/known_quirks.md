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