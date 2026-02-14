"""Modular RNG system for the Pokemon Gen 1 battle engine.

Provides injectable, testable random number generation with support for:
- Deterministic seeded battles (StandardRNG)
- Fixed/queued values for unit tests (FixedRNG)
- Roll recording for audit trails and replays (RecordingRNG)
- Replay from a recorded sequence (ReplayRNG)

Global accessor pattern mirrors engine/events/bus.py.
"""

from __future__ import annotations

import random as _random_module
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional, Sequence, TypeVar

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Context tags
# ---------------------------------------------------------------------------

class RNGContext(Enum):
    """Categories for RNG calls, used for auditing and filtering."""
    BATTLE_MECHANIC = auto()
    DURATION = auto()
    AI_DECISION = auto()
    TEAM_GENERATION = auto()
    IV_GENERATION = auto()


# ---------------------------------------------------------------------------
# Audit record
# ---------------------------------------------------------------------------

@dataclass
class RNGRoll:
    """Single recorded RNG invocation."""
    context: Optional[RNGContext]
    method: str
    args: tuple
    result: Any


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BattleRNG(ABC):
    """Abstract base for all RNG implementations."""

    @abstractmethod
    def random(self, context: Optional[RNGContext] = None) -> float:
        """Return a random float in [0.0, 1.0)."""

    @abstractmethod
    def randint(self, a: int, b: int, context: Optional[RNGContext] = None) -> int:
        """Return a random integer N such that a <= N <= b."""

    @abstractmethod
    def choice(self, seq: Sequence[T], context: Optional[RNGContext] = None) -> T:
        """Return a random element from non-empty sequence."""

    @abstractmethod
    def sample(self, population: Sequence[T], k: int,
               context: Optional[RNGContext] = None) -> list[T]:
        """Return k unique elements from population."""

    def shuffle(self, seq: list, context: Optional[RNGContext] = None) -> None:
        """Shuffle list in-place using Fisher-Yates via self.randint()."""
        for i in range(len(seq) - 1, 0, -1):
            j = self.randint(0, i, context)
            seq[i], seq[j] = seq[j], seq[i]

    @abstractmethod
    def seed(self, value: Any) -> None:
        """Re-seed the RNG."""


# ---------------------------------------------------------------------------
# Standard implementation
# ---------------------------------------------------------------------------

class StandardRNG(BattleRNG):
    """Production RNG wrapping an isolated random.Random() instance."""

    def __init__(self, seed: Any = None):
        self._rng = _random_module.Random(seed)

    def random(self, context: Optional[RNGContext] = None) -> float:
        return self._rng.random()

    def randint(self, a: int, b: int, context: Optional[RNGContext] = None) -> int:
        return self._rng.randint(a, b)

    def choice(self, seq: Sequence[T], context: Optional[RNGContext] = None) -> T:
        return self._rng.choice(seq)

    def sample(self, population: Sequence[T], k: int,
               context: Optional[RNGContext] = None) -> list[T]:
        return self._rng.sample(population, k)

    def seed(self, value: Any) -> None:
        self._rng.seed(value)


# ---------------------------------------------------------------------------
# Fixed / queued values (for tests)
# ---------------------------------------------------------------------------

class FixedRNG(BattleRNG):
    """Returns predetermined values. Supports a fixed default and a queue.

    When the queue has values, they are consumed in FIFO order.
    When the queue is empty, the fixed defaults are used.

    Args:
        random_value: Default for random() calls (float, default 0.5)
        randint_value: Default for randint() calls (int, default 1)
        queue: Optional list of values consumed by any method in order
    """

    def __init__(
        self,
        random_value: float = 0.5,
        randint_value: int = 1,
        queue: Optional[list] = None,
    ):
        self._random_value = random_value
        self._randint_value = randint_value
        self._queue: list = list(queue) if queue else []

    def _next(self, default: Any) -> Any:
        if self._queue:
            return self._queue.pop(0)
        return default

    def random(self, context: Optional[RNGContext] = None) -> float:
        return float(self._next(self._random_value))

    def randint(self, a: int, b: int, context: Optional[RNGContext] = None) -> int:
        return int(self._next(self._randint_value))

    def choice(self, seq: Sequence[T], context: Optional[RNGContext] = None) -> T:
        val = self._next(None)
        if val is None:
            return seq[0]
        # If the queued value is an index, use it; if it's an element, return it
        if isinstance(val, int) and 0 <= val < len(seq):
            return seq[val]
        return val

    def sample(self, population: Sequence[T], k: int,
               context: Optional[RNGContext] = None) -> list[T]:
        return list(population[:k])

    def seed(self, value: Any) -> None:
        pass  # No-op for fixed RNG


# ---------------------------------------------------------------------------
# Recording decorator
# ---------------------------------------------------------------------------

class RecordingRNG(BattleRNG):
    """Wraps any BattleRNG and records every roll."""

    def __init__(self, inner: BattleRNG):
        self._inner = inner
        self.history: list[RNGRoll] = []

    def _record(self, context: Optional[RNGContext], method: str,
                args: tuple, result: Any) -> Any:
        self.history.append(RNGRoll(context=context, method=method,
                                    args=args, result=result))
        return result

    def random(self, context: Optional[RNGContext] = None) -> float:
        result = self._inner.random(context)
        return self._record(context, "random", (), result)

    def randint(self, a: int, b: int, context: Optional[RNGContext] = None) -> int:
        result = self._inner.randint(a, b, context)
        return self._record(context, "randint", (a, b), result)

    def choice(self, seq: Sequence[T], context: Optional[RNGContext] = None) -> T:
        result = self._inner.choice(seq, context)
        return self._record(context, "choice", (tuple(seq),), result)

    def sample(self, population: Sequence[T], k: int,
               context: Optional[RNGContext] = None) -> list[T]:
        result = self._inner.sample(population, k, context)
        return self._record(context, "sample", (tuple(population), k), result)

    def shuffle(self, seq: list, context: Optional[RNGContext] = None) -> None:
        # Delegate to inner which calls randint — those individual calls
        # get recorded by this wrapper if inner is also recorded, or we
        # record via the base shuffle implementation that calls self.randint.
        super().shuffle(seq, context)

    def seed(self, value: Any) -> None:
        self._inner.seed(value)

    def clear(self) -> None:
        """Clear recorded history."""
        self.history.clear()

    def get_history(self, context: Optional[RNGContext] = None) -> list[RNGRoll]:
        """Get history, optionally filtered by context."""
        if context is None:
            return list(self.history)
        return [r for r in self.history if r.context == context]


# ---------------------------------------------------------------------------
# Replay from recorded sequence
# ---------------------------------------------------------------------------

class ReplayRNG(BattleRNG):
    """Replays a recorded sequence of RNGRoll entries.

    Raises IndexError when the sequence is exhausted.
    """

    def __init__(self, rolls: list[RNGRoll]):
        self._rolls = list(rolls)
        self._index = 0

    def _next(self) -> Any:
        if self._index >= len(self._rolls):
            raise IndexError("ReplayRNG: no more recorded rolls to replay")
        result = self._rolls[self._index].result
        self._index += 1
        return result

    def random(self, context: Optional[RNGContext] = None) -> float:
        return self._next()

    def randint(self, a: int, b: int, context: Optional[RNGContext] = None) -> int:
        return self._next()

    def choice(self, seq: Sequence[T], context: Optional[RNGContext] = None) -> T:
        return self._next()

    def sample(self, population: Sequence[T], k: int,
               context: Optional[RNGContext] = None) -> list[T]:
        return self._next()

    def seed(self, value: Any) -> None:
        pass  # No-op for replay


# ---------------------------------------------------------------------------
# Global singleton (mirrors engine/events/bus.py:156-179)
# ---------------------------------------------------------------------------

_global_rng: Optional[BattleRNG] = None


def get_rng() -> BattleRNG:
    """Get the global RNG instance, creating a StandardRNG() if none set."""
    global _global_rng
    if _global_rng is None:
        _global_rng = StandardRNG()
    return _global_rng


def set_rng(rng: BattleRNG) -> None:
    """Set the global RNG instance."""
    global _global_rng
    _global_rng = rng


def reset_rng() -> None:
    """Clear the global RNG instance."""
    global _global_rng
    _global_rng = None
