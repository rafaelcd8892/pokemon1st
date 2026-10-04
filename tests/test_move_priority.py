"""Tests for Gen 1 move priority in turn order (docs/known_quirks.md)."""

from unittest.mock import MagicMock, patch

import pytest

from data.data_loader import create_move
from engine.battle import determine_turn_order, get_effective_priority
from engine.team_battle import BattleAction, TeamBattle
from models.enums import BattleFormat, Status
from models.team import Team
from tests.conftest import create_test_pokemon


def _slow_and_fast():
    slow = create_test_pokemon("Slowpoke", speed=30,
                               moves=[create_move("quick-attack"), create_move("tackle")])
    fast = create_test_pokemon("Jolteon", speed=130,
                               moves=[create_move("tackle"), create_move("counter")])
    return slow, fast


class TestEffectivePriority:

    def test_chosen_move_priority(self):
        slow, _ = _slow_and_fast()
        assert get_effective_priority(slow, slow.moves[0]) == 1
        assert get_effective_priority(slow, slow.moves[1]) == 0

    def test_none_move_is_zero(self):
        slow, _ = _slow_and_fast()
        assert get_effective_priority(slow, None) == 0

    def test_recharging_is_zero(self):
        slow, _ = _slow_and_fast()
        slow.must_recharge = True
        assert get_effective_priority(slow, slow.moves[0]) == 0

    def test_trapped_is_zero(self):
        slow, _ = _slow_and_fast()
        slow.is_trapped = True
        assert get_effective_priority(slow, slow.moves[0]) == 0

    def test_struggle_is_zero(self):
        slow, _ = _slow_and_fast()
        for m in slow.moves:
            m.pp = 0
        assert get_effective_priority(slow, slow.moves[0]) == 0

    def test_locked_move_overrides_choice(self):
        slow, _ = _slow_and_fast()
        slow.multi_turn_move = create_move("thrash")
        slow.multi_turn_counter = 2
        assert get_effective_priority(slow, slow.moves[0]) == 0

    def test_charging_move_overrides_choice(self):
        slow, _ = _slow_and_fast()
        slow.is_charging = True
        slow.charging_move = create_move("solar-beam")
        assert get_effective_priority(slow, slow.moves[0]) == 0

    def test_metronome_is_zero(self):
        mon = create_test_pokemon("Clefable", moves=[create_move("metronome")])
        assert get_effective_priority(mon, mon.moves[0]) == 0


class TestDetermineTurnOrder:

    def test_quick_attack_beats_faster_pokemon(self, seeded_rng):
        slow, fast = _slow_and_fast()
        assert determine_turn_order(slow, fast, slow.moves[0], fast.moves[0]) == (slow, fast)

    def test_counter_goes_after_slower_pokemon(self, seeded_rng):
        slow, fast = _slow_and_fast()
        assert determine_turn_order(slow, fast, slow.moves[1], fast.moves[1]) == (slow, fast)

    def test_quick_attack_beats_counter_regardless_of_order(self, seeded_rng):
        slow, fast = _slow_and_fast()
        assert determine_turn_order(fast, slow, fast.moves[1], slow.moves[0]) == (slow, fast)

    def test_equal_priority_uses_speed(self, seeded_rng):
        slow, fast = _slow_and_fast()
        quick_fast = create_move("quick-attack")
        assert determine_turn_order(slow, fast, slow.moves[0], quick_fast) == (fast, slow)

    def test_paralysis_still_applies_within_same_priority(self, seeded_rng):
        slow, fast = _slow_and_fast()
        fast.status = Status.PARALYSIS  # 130 // 4 = 32 > 30
        slow.base_stats.speed = 40
        assert determine_turn_order(slow, fast, slow.moves[1], fast.moves[0]) == (slow, fast)

    def test_no_moves_keeps_speed_order(self, seeded_rng):
        slow, fast = _slow_and_fast()
        assert determine_turn_order(slow, fast) == (fast, slow)

    def test_logs_priority_reason(self, seeded_rng):
        slow, fast = _slow_and_fast()
        blog = MagicMock()
        with patch("engine.battle.get_battle_logger", return_value=blog):
            determine_turn_order(slow, fast, slow.moves[0], fast.moves[0])
        args = blog.log_turn_order.call_args.args
        assert args[0] == "Slowpoke" and args[-1] == "priority"

    def test_speed_reason_unchanged_without_priority(self, seeded_rng):
        slow, fast = _slow_and_fast()
        blog = MagicMock()
        with patch("engine.battle.get_battle_logger", return_value=blog):
            determine_turn_order(slow, fast, slow.moves[1], fast.moves[0])
        assert blog.log_turn_order.call_args.args[-1] == "speed"


class TestTeamBattlePriority:

    def test_quick_attack_moves_first_in_team_battle(self, seeded_rng):
        slow, fast = _slow_and_fast()
        battle = TeamBattle(Team([slow], "P1"), Team([fast], "P2"),
                            battle_format=BattleFormat.SINGLE, action_delay=0,
                            enable_battle_log=False)
        order = battle.get_turn_order(BattleAction.attack(slow.moves[0]),
                                      BattleAction.attack(fast.moves[0]))
        assert order[0][0] is battle.team1

    def test_switch_still_beats_quick_attack(self, seeded_rng):
        slow, fast = _slow_and_fast()
        backup = create_test_pokemon("Rattata", moves=[create_move("tackle")])
        battle = TeamBattle(Team([slow], "P1"), Team([fast, backup], "P2"),
                            battle_format=BattleFormat.TRIPLE, action_delay=0,
                            enable_battle_log=False)
        order = battle.get_turn_order(BattleAction.attack(slow.moves[0]),
                                      BattleAction.switch(1))
        assert order[0][0] is battle.team2
