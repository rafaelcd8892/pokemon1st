"""Tests for the modular RNG system (engine/rng.py)."""

import pytest
from engine.rng import (
    BattleRNG,
    StandardRNG,
    FixedRNG,
    RecordingRNG,
    ReplayRNG,
    RNGContext,
    RNGRoll,
    get_rng,
    set_rng,
    reset_rng,
)


# ---------------------------------------------------------------------------
# StandardRNG
# ---------------------------------------------------------------------------

class TestStandardRNG:
    """Tests for StandardRNG (production implementation)."""

    def test_same_seed_produces_same_sequence(self):
        rng1 = StandardRNG(seed=42)
        rng2 = StandardRNG(seed=42)
        for _ in range(20):
            assert rng1.random() == rng2.random()

    def test_different_seeds_diverge(self):
        rng1 = StandardRNG(seed=42)
        rng2 = StandardRNG(seed=99)
        results1 = [rng1.random() for _ in range(10)]
        results2 = [rng2.random() for _ in range(10)]
        assert results1 != results2

    def test_randint_bounds(self):
        rng = StandardRNG(seed=0)
        for _ in range(100):
            val = rng.randint(1, 6)
            assert 1 <= val <= 6

    def test_random_bounds(self):
        rng = StandardRNG(seed=0)
        for _ in range(100):
            val = rng.random()
            assert 0.0 <= val < 1.0

    def test_choice_returns_element_from_seq(self):
        rng = StandardRNG(seed=0)
        items = ["a", "b", "c"]
        for _ in range(20):
            assert rng.choice(items) in items

    def test_sample_returns_unique_elements(self):
        rng = StandardRNG(seed=0)
        items = list(range(10))
        result = rng.sample(items, 5)
        assert len(result) == 5
        assert len(set(result)) == 5
        assert all(r in items for r in result)

    def test_shuffle_changes_order(self):
        rng = StandardRNG(seed=42)
        items = list(range(20))
        original = items.copy()
        rng.shuffle(items)
        # With 20 items, extremely unlikely to be the same
        assert items != original

    def test_seed_resets_sequence(self):
        rng = StandardRNG(seed=42)
        first = [rng.random() for _ in range(5)]
        rng.seed(42)
        second = [rng.random() for _ in range(5)]
        assert first == second

    def test_context_parameter_is_ignored_for_output(self):
        rng1 = StandardRNG(seed=42)
        rng2 = StandardRNG(seed=42)
        assert rng1.random(RNGContext.BATTLE_MECHANIC) == rng2.random(RNGContext.AI_DECISION)


# ---------------------------------------------------------------------------
# FixedRNG
# ---------------------------------------------------------------------------

class TestFixedRNG:
    """Tests for FixedRNG (test double)."""

    def test_fixed_random_value(self):
        rng = FixedRNG(random_value=0.75)
        assert rng.random() == 0.75
        assert rng.random() == 0.75  # Always returns same value

    def test_fixed_randint_value(self):
        rng = FixedRNG(randint_value=3)
        assert rng.randint(1, 10) == 3
        assert rng.randint(1, 10) == 3

    def test_queue_consumed_in_order(self):
        rng = FixedRNG(queue=[0.1, 0.2, 0.3])
        assert rng.random() == 0.1
        assert rng.random() == 0.2
        assert rng.random() == 0.3

    def test_queue_falls_back_to_default_when_empty(self):
        rng = FixedRNG(random_value=0.99, queue=[0.1])
        assert rng.random() == 0.1   # From queue
        assert rng.random() == 0.99  # Fallback to default

    def test_choice_returns_queued_value(self):
        items = ["a", "b", "c"]
        rng = FixedRNG(queue=["b"])
        assert rng.choice(items) == "b"

    def test_choice_returns_first_element_by_default(self):
        items = ["a", "b", "c"]
        rng = FixedRNG()
        assert rng.choice(items) == "a"

    def test_sample_returns_first_k(self):
        items = [1, 2, 3, 4, 5]
        rng = FixedRNG()
        assert rng.sample(items, 3) == [1, 2, 3]

    def test_seed_is_noop(self):
        rng = FixedRNG(random_value=0.5)
        rng.seed(42)
        assert rng.random() == 0.5


# ---------------------------------------------------------------------------
# RecordingRNG
# ---------------------------------------------------------------------------

class TestRecordingRNG:
    """Tests for RecordingRNG (decorator)."""

    def test_records_history(self):
        inner = StandardRNG(seed=42)
        rng = RecordingRNG(inner)
        rng.random(RNGContext.BATTLE_MECHANIC)
        rng.randint(1, 6, RNGContext.DURATION)
        assert len(rng.history) == 2

    def test_records_correct_fields(self):
        inner = StandardRNG(seed=42)
        rng = RecordingRNG(inner)
        result = rng.randint(1, 100, RNGContext.BATTLE_MECHANIC)
        roll = rng.history[0]
        assert roll.context == RNGContext.BATTLE_MECHANIC
        assert roll.method == "randint"
        assert roll.args == (1, 100)
        assert roll.result == result

    def test_delegates_to_inner(self):
        inner = StandardRNG(seed=42)
        direct = StandardRNG(seed=42)
        rng = RecordingRNG(inner)
        assert rng.random() == direct.random()

    def test_filter_by_context(self):
        inner = StandardRNG(seed=42)
        rng = RecordingRNG(inner)
        rng.random(RNGContext.BATTLE_MECHANIC)
        rng.random(RNGContext.AI_DECISION)
        rng.random(RNGContext.BATTLE_MECHANIC)
        battle = rng.get_history(RNGContext.BATTLE_MECHANIC)
        assert len(battle) == 2
        ai = rng.get_history(RNGContext.AI_DECISION)
        assert len(ai) == 1

    def test_clear_history(self):
        inner = StandardRNG(seed=42)
        rng = RecordingRNG(inner)
        rng.random()
        rng.clear()
        assert len(rng.history) == 0

    def test_shuffle_records_individual_randint_calls(self):
        inner = FixedRNG(randint_value=0)
        rng = RecordingRNG(inner)
        items = [1, 2, 3, 4]
        rng.shuffle(items, RNGContext.TEAM_GENERATION)
        # Fisher-Yates on 4 elements makes 3 randint calls
        assert len(rng.history) == 3
        assert all(r.method == "randint" for r in rng.history)


# ---------------------------------------------------------------------------
# ReplayRNG
# ---------------------------------------------------------------------------

class TestReplayRNG:
    """Tests for ReplayRNG (sequence replay)."""

    def test_replays_exact_sequence(self):
        inner = StandardRNG(seed=42)
        recorder = RecordingRNG(inner)
        original = [recorder.randint(1, 100) for _ in range(5)]

        replay = ReplayRNG(recorder.history)
        replayed = [replay.randint(1, 100) for _ in range(5)]
        assert original == replayed

    def test_raises_on_exhaustion(self):
        rolls = [RNGRoll(context=None, method="random", args=(), result=0.5)]
        rng = ReplayRNG(rolls)
        rng.random()
        with pytest.raises(IndexError):
            rng.random()


# ---------------------------------------------------------------------------
# Global accessors
# ---------------------------------------------------------------------------

class TestGlobalAccessors:
    """Tests for get_rng / set_rng / reset_rng."""

    def teardown_method(self):
        reset_rng()

    def test_get_rng_creates_default(self):
        reset_rng()
        rng = get_rng()
        assert isinstance(rng, StandardRNG)

    def test_set_rng_overrides(self):
        fixed = FixedRNG(random_value=0.42)
        set_rng(fixed)
        assert get_rng() is fixed
        assert get_rng().random() == 0.42

    def test_reset_rng_clears(self):
        set_rng(FixedRNG())
        reset_rng()
        # Next get_rng() should create a fresh StandardRNG
        rng = get_rng()
        assert isinstance(rng, StandardRNG)


# ---------------------------------------------------------------------------
# Integration: determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    """Verify that same seed produces same RNG sequence across resets."""

    def teardown_method(self):
        reset_rng()

    def test_same_seed_same_sequence(self):
        set_rng(StandardRNG(seed=12345))
        seq1 = [get_rng().randint(1, 255) for _ in range(50)]

        set_rng(StandardRNG(seed=12345))
        seq2 = [get_rng().randint(1, 255) for _ in range(50)]

        assert seq1 == seq2
