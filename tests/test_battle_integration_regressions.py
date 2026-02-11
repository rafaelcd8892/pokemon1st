"""Integration/regression coverage for battle engine robustness.

Priority: strengthen end-to-end turn flow tests and encode known gaps
as strict xfail regression tests.
"""

from unittest.mock import patch

from engine.battle import apply_damage_to_target, execute_turn
from engine.damage import calculate_critical_hit
from engine.status import apply_end_turn_status_damage
from engine.team_battle import BattleAction, TeamBattle
from models.enums import BattleFormat, MoveCategory, Status, Type
from models.pokemon import Pokemon
from models.stats import Stats
from models.team import Team
from tests.conftest import create_test_move


def _poke(
    name: str,
    *,
    types: list[Type] | None = None,
    hp: int = 120,
    attack: int = 90,
    defense: int = 90,
    special: int = 90,
    speed: int = 90,
    moves=None,
    level: int = 50,
    use_calculated_stats: bool = False,
) -> Pokemon:
    """Small local helper for integration scenarios."""
    if types is None:
        types = [Type.NORMAL]
    if moves is None:
        moves = [create_test_move(name="Tackle", power=40)]

    stats = Stats(hp=hp, attack=attack, defense=defense, special=special, speed=speed)
    return Pokemon(
        name=name,
        types=types,
        stats=stats,
        moves=moves,
        level=level,
        use_calculated_stats=use_calculated_stats,
    )


class TestBattleIntegrationFlow:
    """High-value integration tests for full-turn resolution."""

    def test_switch_resolves_before_attack(self):
        """A switch action must resolve before the opponent's attack."""
        switcher_active = _poke("SwitcherA", hp=90, speed=120)
        switcher_bench = _poke("SwitcherB", hp=140, speed=30)

        strong_hit = create_test_move(
            name="Body Slam",
            move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            power=120,
            accuracy=100,
        )
        attacker = _poke("Aggressor", hp=150, attack=150, speed=100, moves=[strong_hit])

        team1 = Team([switcher_active, switcher_bench], "Team1")
        team2 = Team([attacker], "Team2")

        battle = TeamBattle(
            team1,
            team2,
            battle_format=BattleFormat.FULL,
            action_delay=0,
            enable_battle_log=False,
        )

        action1 = BattleAction.switch(1)
        action2 = BattleAction.attack(strong_hit)

        with patch("engine.damage.calculate_critical_hit", return_value=False), patch(
            "engine.damage.get_random_factor", return_value=1.0
        ):
            battle.execute_turn_pair(action1, action2)

        assert team1.active_pokemon.name == "SwitcherB"
        assert switcher_active.current_hp == switcher_active.max_hp
        assert switcher_bench.current_hp < switcher_bench.max_hp

    def test_forced_switch_happens_before_next_turn_actions(self):
        """After a KO, forced switch should occur before requesting next actions."""
        fainted = _poke("Lead", hp=1, speed=50)
        bench = _poke("Backup", hp=120, speed=60)

        ko_move = create_test_move(
            name="Mega Punch",
            move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            power=200,
            accuracy=100,
        )
        enemy = _poke("Enemy", hp=120, attack=180, speed=100, moves=[ko_move])

        team1 = Team([fainted, bench], "P1")
        team2 = Team([enemy], "P2")

        battle = TeamBattle(
            team1,
            team2,
            battle_format=BattleFormat.FULL,
            max_turns=3,
            action_delay=0,
            enable_battle_log=False,
        )

        def p2_action(_team, _opp):
            return BattleAction.attack(ko_move)

        def forced_switch(_team):
            return 1

        with patch("engine.damage.calculate_critical_hit", return_value=False), patch(
            "engine.damage.get_random_factor", return_value=1.0
        ):
            battle.execute_turn_pair(BattleAction.attack(fainted.moves[0]), p2_action(team2, team1))
            assert team1.active_pokemon.name == "Lead"

            # Simulate the next loop iteration forced-switch phase.
            if battle.needs_forced_switch(team1):
                team1.switch_pokemon(forced_switch(team1))

        assert team1.active_pokemon.name == "Backup"
        assert fainted.current_hp == 0

    def test_team_battle_writes_detailed_move_entries(self):
        """TeamBattle and battle engine should share the same detailed logger."""
        tackle = create_test_move(
            name="Tackle",
            move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            power=50,
            accuracy=100,
        )
        splash = create_test_move(
            name="Splash",
            move_type=Type.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=100,
        )
        p1 = _poke("P1Mon", moves=[tackle], speed=120, attack=120)
        p2 = _poke("P2Mon", moves=[splash], speed=40, hp=120, defense=60)

        battle = TeamBattle(
            Team([p1], "T1"),
            Team([p2], "T2"),
            battle_format=BattleFormat.SINGLE,
            action_delay=0,
            enable_battle_log=True,
        )

        with patch("engine.damage.calculate_critical_hit", return_value=False), patch(
            "engine.damage.get_random_factor", return_value=1.0
        ):
            battle.execute_turn_pair(BattleAction.attack(tackle), BattleAction.attack(splash))

        move_entries = [e for e in battle.battle_logger.entries if e.action_type == "move"]
        assert move_entries, "Expected detailed move entries in battle logger"

    def test_move_entries_include_side_for_duplicate_names(self):
        """Move events should include side tags even when names are duplicated."""
        lick = create_test_move(
            name="Lick",
            move_type=Type.GHOST,
            category=MoveCategory.PHYSICAL,
            power=20,
            accuracy=100,
        )
        same_name_p1 = _poke("Haunter", types=[Type.GHOST], moves=[lick], speed=120, attack=120, hp=120)
        same_name_p2 = _poke("Haunter", types=[Type.GHOST], moves=[lick], speed=30, defense=60, hp=120)

        battle = TeamBattle(
            Team([same_name_p1], "Team1"),
            Team([same_name_p2], "Team2"),
            battle_format=BattleFormat.SINGLE,
            action_delay=0,
            enable_battle_log=True,
        )

        with patch("engine.damage.calculate_critical_hit", return_value=False), patch(
            "engine.damage.get_random_factor", return_value=1.0
        ):
            battle.execute_turn_pair(BattleAction.attack(lick), BattleAction.attack(lick))

        move_entries = [e for e in battle.battle_logger.entries if e.action_type == "move"]
        assert move_entries
        assert any(e.pokemon_side == "P1" for e in move_entries)
        assert any(e.pokemon_side == "P2" for e in move_entries)

    def test_substitute_logs_as_self_target(self):
        """Substitute should always log the user as target for audit consistency."""
        substitute = create_test_move(
            name="Substitute",
            move_type=Type.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=100,
        )
        splash = create_test_move(
            name="Splash",
            move_type=Type.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=100,
        )
        p1 = _poke("Wigglytuff", hp=200, moves=[splash], speed=30)
        p2 = _poke("Hitmonchan", hp=160, moves=[substitute], speed=120)

        battle = TeamBattle(
            Team([p1], "Team1"),
            Team([p2], "Team2"),
            battle_format=BattleFormat.SINGLE,
            action_delay=0,
            enable_battle_log=True,
        )

        battle.execute_turn_pair(BattleAction.attack(splash), BattleAction.attack(substitute))

        substitute_entries = [
            e for e in battle.battle_logger.entries
            if e.action_type == "move" and e.details.get("move") == "Substitute"
        ]
        assert substitute_entries
        assert substitute_entries[0].pokemon == substitute_entries[0].target

    def test_move_logs_blocked_by_invulnerability_result(self):
        """When target is semi-invulnerable, move log should capture explicit result."""
        tackle = create_test_move(
            name="Tackle",
            move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            power=40,
            accuracy=100,
        )
        splash = create_test_move(
            name="Splash",
            move_type=Type.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=100,
        )
        attacker = _poke("Attacker", moves=[tackle], speed=120)
        defender = _poke("Defender", moves=[splash], speed=10)
        defender.is_semi_invulnerable = True

        battle = TeamBattle(
            Team([attacker], "P1"),
            Team([defender], "P2"),
            battle_format=BattleFormat.SINGLE,
            action_delay=0,
            enable_battle_log=True,
        )

        battle.execute_turn_pair(BattleAction.attack(tackle), BattleAction.attack(splash))

        move_entries = [
            e for e in battle.battle_logger.entries
            if e.action_type == "move" and e.pokemon == "Attacker" and e.details.get("move") == "Tackle"
        ]
        assert move_entries
        assert move_entries[0].details.get("result") == "blocked_by_invulnerability"

    def test_charge_move_logs_single_event_on_charge_turn(self):
        """Charge turn should emit exactly one move event for the charging move."""
        dig = create_test_move(
            name="Dig",
            move_type=Type.GROUND,
            category=MoveCategory.PHYSICAL,
            power=80,
            accuracy=100,
        )
        splash = create_test_move(
            name="Splash",
            move_type=Type.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=100,
        )
        user = _poke("Sandshrew", moves=[dig], speed=120)
        foe = _poke("Bulbasaur", moves=[splash], speed=20)

        battle = TeamBattle(
            Team([user], "P1"),
            Team([foe], "P2"),
            battle_format=BattleFormat.SINGLE,
            action_delay=0,
            enable_battle_log=True,
        )

        battle.execute_turn_pair(BattleAction.attack(dig), BattleAction.attack(splash))
        battle.execute_turn_pair(BattleAction.attack(dig), BattleAction.attack(splash))

        dig_turn_1 = [
            e for e in battle.battle_logger.entries
            if e.action_type == "move" and e.turn == 1 and e.details.get("move") == "Dig"
        ]
        assert len(dig_turn_1) == 1
        assert dig_turn_1[0].details.get("result") == "charge_start"


class TestRegressionSpecs:
    """Known gaps encoded as strict xfails (expected behavior specs)."""

    def test_critical_hit_should_not_depend_on_level_for_same_species(self):
        """For equal species base speed, crit probability should not scale with level."""
        fast_stats = Stats(hp=35, attack=55, defense=40, special=50, speed=130)
        move = create_test_move(name="Quick Attack", power=40)

        low_level = Pokemon(
            "Jolteon-Low",
            [Type.ELECTRIC],
            fast_stats,
            [move],
            level=5,
            use_calculated_stats=True,
        )
        high_level = Pokemon(
            "Jolteon-High",
            [Type.ELECTRIC],
            fast_stats,
            [move],
            level=100,
            use_calculated_stats=True,
        )

        # 0.30 should be above Gen1 base-speed chance for 130 (130/512 ~= 0.254)
        with patch("engine.damage.random.random", return_value=0.30):
            assert calculate_critical_hit(low_level) is False
            assert calculate_critical_hit(high_level) is False

    def test_trapped_state_should_decay_even_if_original_trapper_context_changes(self):
        """Trap timers should not require the original trapper to remain as active context."""
        trapper = _poke("Trapper")
        trapped = _poke("Victim")
        other = _poke("Other")

        trapped.is_trapped = True
        trapped.trap_turns = 1
        trapped.trapped_by = trapper

        # End-of-turn in a changed context should still clear stale trap state.
        from engine.battle import _apply_trapping_effects

        _apply_trapping_effects(trapped, other)

        assert trapped.is_trapped is False
        assert trapped.trapped_by is None

    def test_apply_damage_returns_effective_damage_amount(self):
        """Damage application should return actual HP removed from target."""
        target = _poke("Tank", hp=30)
        target.current_hp = 10

        applied = apply_damage_to_target(target, 50, is_physical=True)

        assert target.current_hp == 0
        assert applied == 10

    def test_team_battle_metronome_should_execute_selected_move(self):
        """In team battle, Metronome should resolve into a real move effect."""
        metronome = create_test_move(
            name="Metronome",
            move_type=Type.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=100,
            pp=10,
        )
        scratch = create_test_move(
            name="Scratch",
            move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            power=40,
            accuracy=100,
        )
        dragon_rage = create_test_move(
            name="Dragon Rage",
            move_type=Type.DRAGON,
            category=MoveCategory.SPECIAL,
            power=1,
            accuracy=100,
        )
        splash = create_test_move(
            name="Splash",
            move_type=Type.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=100,
        )

        user = _poke("User", moves=[metronome], speed=120)
        foe = _poke("Foe", moves=[splash, dragon_rage, scratch], hp=120, defense=60, speed=30)

        team1 = Team([user], "P1")
        team2 = Team([foe], "P2")

        battle = TeamBattle(team1, team2, battle_format=BattleFormat.SINGLE, action_delay=0, enable_battle_log=False)

        with patch("engine.move_effects.random.choice", return_value=dragon_rage):
            battle.execute_turn_pair(BattleAction.attack(metronome), BattleAction.attack(splash))

        assert foe.current_hp < foe.max_hp

    def test_transform_state_should_reset_after_switch(self):
        """Switching out should restore original form after Transform."""
        transform = create_test_move(
            name="Transform",
            move_type=Type.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=100,
        )
        filler = create_test_move(name="Tackle", power=40)

        ditto = _poke("Ditto", types=[Type.NORMAL], special=80, moves=[transform])
        target = _poke("Target", types=[Type.FIRE, Type.FLYING], special=120, moves=[filler])
        bench = _poke("Bench", types=[Type.WATER], moves=[filler])

        execute_turn(ditto, target, transform)
        assert ditto.types == [Type.FIRE, Type.FLYING]

        team = Team([ditto, bench], "P1")
        team.switch_pokemon(1)
        team.switch_pokemon(0)

        assert ditto.types == [Type.NORMAL]

    def test_end_turn_status_damage_should_skip_fainted_targets(self, capsys):
        """No status damage message/effect should be emitted for fainted Pokemon."""
        fainted = _poke("Fainted", hp=100)
        fainted.current_hp = 0
        fainted.status = Status.BURN

        apply_end_turn_status_damage(fainted)
        out = capsys.readouterr().out

        assert out == ""
        assert fainted.current_hp == 0

    def test_self_destruct_logs_move_even_on_immunity(self):
        """Self Destruct should always be logged, even if target is immune."""
        self_destruct = create_test_move(
            name="Self Destruct",
            move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            power=200,
            accuracy=100,
        )
        splash = create_test_move(
            name="Splash",
            move_type=Type.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=100,
        )
        user = _poke("Boomer", types=[Type.NORMAL], moves=[self_destruct], speed=120)
        target = _poke("Ghosty", types=[Type.GHOST], moves=[splash], hp=120, speed=10)

        battle = TeamBattle(
            Team([user], "P1"),
            Team([target], "P2"),
            battle_format=BattleFormat.SINGLE,
            action_delay=0,
            enable_battle_log=True,
        )

        battle.execute_turn_pair(BattleAction.attack(self_destruct), BattleAction.attack(splash))

        sd_logs = [
            e for e in battle.battle_logger.entries
            if e.action_type == "move" and e.pokemon == "Boomer" and e.details.get("move") == "Self Destruct"
        ]
        assert sd_logs, "Expected Self Destruct move event in logger"

    def test_horn_drill_is_treated_as_ohko_move(self):
        """Horn Drill should resolve through OHKO logic, not normal damage formula."""
        horn_drill = create_test_move(
            name="Horn Drill",
            move_type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            power=1,
            accuracy=0,  # accuracy=0 means always hit in this engine
        )
        splash = create_test_move(
            name="Splash",
            move_type=Type.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=100,
        )
        attacker = _poke("Nidoking", moves=[horn_drill], speed=120)
        defender = _poke("Victim", moves=[splash], hp=140, speed=30)

        execute_turn(attacker, defender, horn_drill)

        assert defender.current_hp == 0
