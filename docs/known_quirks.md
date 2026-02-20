# Known Quirks — Gen 1 Mechanics Policy

This document defines which Gen 1 quirks we **replicate**, **approximate**, or **ignore**.
Agents must follow this policy. If a ticket requires changing it, update this document and add a decision entry.

Policy lock date: `2026-02-20` (`FID-001`, `FID-002`)

## Status legend
- ✅ Replicate
- ⚠️ Approximate
- ❌ Ignore

## Mechanics matrix (policy + grounding)
| Mechanic | Policy | Implementation map | Source refs | Notes |
| --- | --- | --- | --- | --- |
| Damage rounding rules | ⚠️ Approximate | `engine/damage.py` (`calculate_base_damage`, `calculate_damage_with_breakdown`) | S1, S2 | Integer/floor behavior is deterministic but not fully hardware-accurate. |
| Stat modifiers rounding | ⚠️ Approximate | `engine/stat_modifiers.py` (`apply_stat_stage_to_stat`) | S1, S2 | Uses integer multiply/floor division by stage fractions. |
| Crit rate based on Speed | ✅ Replicate | `engine/damage.py` (`calculate_critical_hit`) | S1, S2, S3 | Uses base species Speed with Gen 1 crit path. |
| High-crit moves behavior | ⚠️ Approximate | `engine/damage.py` (`calculate_critical_hit`) | S1, S2, S3 | Move-specific high-crit boosts are not yet split from base crit path. |
| 1/256 miss glitch | ❌ Ignore | `engine/battle.py` (`_check_accuracy`) | S1, S2, S3 | Uses percentage roll (`1..100`) and intentionally does not emulate byte-overflow miss behavior. |
| Accuracy/evasion stage behavior | ⚠️ Approximate | `engine/stat_modifiers.py` (`get_accuracy_multiplier`, `get_stat_multiplier`), `engine/battle.py` (`_check_accuracy`) | S1, S2, S3 | Stage math is clamped and deterministic, not cycle-perfect hardware emulation. |
| Freeze permanence (no natural thaw) | ✅ Replicate | `engine/status.py` (`apply_status_effects`), `engine/battle.py` (`_execute_normal_attack`, `_deal_damage_with_messages`) | S1, S2 | Frozen Pokemon do not thaw naturally; Fire-type hit cures freeze. |
| Freeze overriding other statuses | ⚠️ Approximate | `models/pokemon.py` (`apply_status`), `engine/battle.py` (`_apply_move_status_effect`) | S1, S2 | Enforces one-major-status rule; precedence edge cases are not fully modeled. |
| Wrap/Fire Spin lock behavior | ⚠️ Approximate | `engine/battle.py` (`_handle_trapping_move`, `_apply_trapping_effects`, trapped check in `execute_turn`) | S1, S2, S3 | Core lock/duration present; exact Gen 1 turn-order edge cases deferred to `FID-010`. |
| Hyper Beam recharge behavior | ⚠️ Approximate | `engine/battle.py` (`_handle_recharge_move`, `_handle_recharge_state`) | S1, S2, S3 | Recharge on non-KO path implemented; full edge matrix deferred to `FID-011`. |
| Bide store/release behavior | ⚠️ Approximate | `engine/battle.py` (`_execute_normal_attack`), `engine/move_effects.py` (`is_special_move`, `execute_special_move`) | S1, S2, S3 | Currently treated as a regular attack path; exact Gen 1 Bide lock/store/retaliate behavior is deferred to `FID-023`. |
| Focus Energy bug | ✅ Replicate | `engine/move_effects.py` (`execute_special_move`), `engine/damage.py` (`calculate_critical_hit`) | S1, S2, S3 | Focus Energy flag applies Gen 1 bug behavior (crit chance divided instead of increased). |
| Leech Seed + Toxic interaction | ❌ Ignore | `engine/move_effects.py` (`execute_special_move`), `engine/battle.py` (`_apply_leech_seed_effects`), `engine/status.py` (`apply_end_turn_status_damage`) | S1, S2, S3 | Toxic counter interaction is intentionally not modeled yet; revisit in `FID-020`. |

## Source references
- `S1`: Pokemon Red/Blue disassembly (`pret/pokered`) battle routines and status/move logic.
- `S2`: Bulbapedia reference pages for Generation I battle mechanics (critical hit, freeze, trapping, Hyper Beam, accuracy, Focus Energy).
- `S3`: Smogon RBY mechanics analyses and competitive mechanics write-ups.
