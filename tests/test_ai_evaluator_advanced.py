"""Tests for Phase 2 evaluator functions: threat_score, score_switch_target, should_switch."""

import pytest
from models.enums import Type, MoveCategory, Status
from models.team import Team
from tests.conftest import create_test_pokemon, create_test_move
from engine.ai.evaluator import threat_score, score_switch_target, should_switch


class TestThreatScore:
    """Tests for threat_score — how dangerous is attacker to defender?"""

    def test_high_threat_super_effective(self):
        """Super-effective attacker with strong moves = high threat."""
        attacker = create_test_pokemon(
            name="Jolteon", types=[Type.ELECTRIC], special=110,
            moves=[
                create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95),
            ]
        )
        defender = create_test_pokemon(
            name="Gyarados", types=[Type.WATER, Type.FLYING], hp=95, special=60,
        )
        score = threat_score(attacker, defender)
        assert score > 0.5  # Should be very threatening

    def test_low_threat_resisted(self):
        """Attacker whose moves are resisted = low threat."""
        attacker = create_test_pokemon(
            name="Pikachu", types=[Type.ELECTRIC], special=50,
            moves=[
                create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95),
            ]
        )
        defender = create_test_pokemon(
            name="Rhydon", types=[Type.GROUND, Type.ROCK], hp=105, special=45,
        )
        score = threat_score(attacker, defender)
        assert score == 0.0  # Electric is immune to Ground

    def test_zero_threat_from_fainted(self):
        """Fainted defender has 0 threat score."""
        attacker = create_test_pokemon(types=[Type.NORMAL])
        defender = create_test_pokemon(types=[Type.NORMAL])
        defender.current_hp = 0
        assert threat_score(attacker, defender) == 0.0

    def test_ko_threat_above_one(self):
        """A move that can KO produces threat >= 1.0."""
        attacker = create_test_pokemon(
            name="Alakazam", types=[Type.PSYCHIC], special=135,
            moves=[
                create_test_move("Psychic", Type.PSYCHIC, MoveCategory.SPECIAL, 90),
            ]
        )
        defender = create_test_pokemon(
            name="WeakMon", types=[Type.FIGHTING], hp=50, special=30,
        )
        score = threat_score(attacker, defender)
        assert score >= 1.0

    def test_no_pp_moves_zero_threat(self):
        """If all moves have 0 PP, threat is 0."""
        attacker = create_test_pokemon(
            types=[Type.NORMAL],
            moves=[create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40, pp=0)]
        )
        defender = create_test_pokemon(types=[Type.NORMAL])
        assert threat_score(attacker, defender) == 0.0


class TestScoreSwitchTarget:
    """Tests for score_switch_target — how good is this switch-in?"""

    def test_resist_scores_higher_than_weak(self):
        """A candidate that resists the opponent's STAB scores higher."""
        opponent = create_test_pokemon(
            name="Charizard", types=[Type.FIRE, Type.FLYING], attack=84, special=85,
            moves=[
                create_test_move("Flamethrower", Type.FIRE, MoveCategory.SPECIAL, 95),
            ]
        )
        own_active = create_test_pokemon(name="Current", types=[Type.GRASS])

        # Good switch-in: Water type resists Fire
        water_mon = create_test_pokemon(
            name="Blastoise", types=[Type.WATER], hp=79, special=85,
            moves=[
                create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95),
            ]
        )
        # Bad switch-in: Grass type is weak to Fire
        grass_mon = create_test_pokemon(
            name="Venusaur", types=[Type.GRASS, Type.POISON], hp=80, special=80,
            moves=[
                create_test_move("Razor Leaf", Type.GRASS, MoveCategory.PHYSICAL, 55),
            ]
        )

        water_score = score_switch_target(water_mon, opponent, own_active)
        grass_score = score_switch_target(grass_mon, opponent, own_active)
        assert water_score > grass_score

    def test_healthy_preferred_over_low_hp(self):
        """Same type matchup but healthier candidate scores higher."""
        opponent = create_test_pokemon(
            name="Opponent", types=[Type.NORMAL], attack=80,
            moves=[create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40)]
        )
        own_active = create_test_pokemon(name="Current", types=[Type.NORMAL])

        healthy = create_test_pokemon(name="Healthy", types=[Type.ROCK], hp=100)
        healthy.current_hp = 100

        damaged = create_test_pokemon(name="Damaged", types=[Type.ROCK], hp=100)
        damaged.current_hp = 20

        assert score_switch_target(healthy, opponent, own_active) > \
               score_switch_target(damaged, opponent, own_active)


class TestShouldSwitch:
    """Tests for should_switch — the switching decision function."""

    def test_switch_when_threatened(self):
        """Should recommend switch when active is heavily threatened."""
        # Active is VERY threatened: Grass vs Water attacker with strong Electric
        active = create_test_pokemon(
            name="Gyarados", types=[Type.WATER, Type.FLYING], hp=95, special=60,
            moves=[create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95)]
        )
        reserve = create_test_pokemon(
            name="Rhydon", types=[Type.GROUND, Type.ROCK], hp=105, special=45,
            moves=[create_test_move("Earthquake", Type.GROUND, MoveCategory.PHYSICAL, 100)]
        )
        opponent = create_test_pokemon(
            name="Jolteon", types=[Type.ELECTRIC], special=110,
            moves=[create_test_move("Thunderbolt", Type.ELECTRIC, MoveCategory.SPECIAL, 95)]
        )
        team = Team([active, reserve], "Player")

        do_switch, idx = should_switch(team, opponent, threshold=0.35)
        # Jolteon is 4x effective vs Gyarados, Rhydon is immune to Electric
        assert do_switch is True
        assert idx == 1

    def test_no_switch_when_safe(self):
        """Should not switch when active is not threatened."""
        active = create_test_pokemon(
            name="Snorlax", types=[Type.NORMAL], hp=160, special=65,
            moves=[create_test_move("Body Slam", Type.NORMAL, MoveCategory.PHYSICAL, 85)]
        )
        reserve = create_test_pokemon(
            name="Reserve", types=[Type.WATER], hp=80,
            moves=[create_test_move("Surf", Type.WATER, MoveCategory.SPECIAL, 95)]
        )
        opponent = create_test_pokemon(
            name="Oddish", types=[Type.GRASS, Type.POISON], attack=50, special=75,
            moves=[create_test_move("Absorb", Type.GRASS, MoveCategory.SPECIAL, 20)]
        )
        team = Team([active, reserve], "Player")

        do_switch, idx = should_switch(team, opponent, threshold=0.35)
        assert do_switch is False

    def test_no_switch_when_no_reserves(self):
        """Cannot switch when team has no reserves."""
        active = create_test_pokemon(
            name="Solo", types=[Type.NORMAL], hp=100,
            moves=[create_test_move("Tackle", Type.NORMAL, MoveCategory.PHYSICAL, 40)]
        )
        opponent = create_test_pokemon(
            name="Threat", types=[Type.FIGHTING], attack=130,
            moves=[create_test_move("Close Combat", Type.FIGHTING, MoveCategory.PHYSICAL, 120)]
        )
        team = Team([active], "Player")

        do_switch, idx = should_switch(team, opponent, threshold=0.35)
        assert do_switch is False
        assert idx is None

    def test_no_switch_when_reserves_worse(self):
        """Should not switch if no reserve is meaningfully better."""
        active = create_test_pokemon(
            name="Tauros", types=[Type.NORMAL], hp=75, attack=100,
            moves=[create_test_move("Body Slam", Type.NORMAL, MoveCategory.PHYSICAL, 85)]
        )
        reserve = create_test_pokemon(
            name="Raticate", types=[Type.NORMAL], hp=55, attack=81,
            moves=[create_test_move("Hyper Fang", Type.NORMAL, MoveCategory.PHYSICAL, 80)]
        )
        opponent = create_test_pokemon(
            name="Machamp", types=[Type.FIGHTING], attack=130,
            moves=[create_test_move("Submission", Type.FIGHTING, MoveCategory.PHYSICAL, 80)]
        )
        team = Team([active, reserve], "Player")

        do_switch, idx = should_switch(team, opponent, threshold=0.35)
        # Reserve (Normal) isn't better than active (Normal) vs Fighting
        # Both are equally weak to Fighting — no benefit to switching
        assert do_switch is False
