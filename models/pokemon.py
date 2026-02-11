from typing import Optional
from models.enums import Type, Status, StatType
from models.stats import Stats
from models.move import Move
from models.ivs import IVs
import random


class Pokemon:
    """
    Represents a Pokemon with stats, moves, and battle state.

    Stats can be calculated from base stats + level + IVs (Gen 1 formula)
    or used directly (legacy mode for tests/debugging).
    """

    def __init__(
        self,
        name: str,
        types: list[Type],
        stats: Stats,
        moves: list[Move],
        level: int = 50,
        ivs: Optional[IVs] = None,
        evs: Optional[dict] = None,
        use_calculated_stats: bool = True
    ):
        """
        Initialize a Pokemon.

        Args:
            name: Pokemon name
            types: List of Type enums
            stats: Base stats (species stats from data)
            moves: List of Move objects
            level: Pokemon level (1-100), defaults to 50
            ivs: Individual Values, defaults to perfect IVs
            evs: Effort Values dict, defaults to max EVs if use_calculated_stats
            use_calculated_stats: If True, calculate stats from formula.
                                  If False, use stats directly (legacy mode).
        """
        self.name = name
        self.types = types
        self.level = level
        self.moves = moves

        # Store species base stats separately
        self._species_base_stats = stats

        # IVs - default to perfect for competitive battles
        self.ivs = ivs if ivs is not None else IVs.perfect()

        # EVs - stored for reference (None means use defaults)
        self.evs = evs

        # Calculate or use stats directly
        self._use_calculated_stats = use_calculated_stats
        if use_calculated_stats:
            from engine.stat_calculator import calculate_stats
            self._calculated_stats = calculate_stats(
                stats, self.ivs, level, evs, use_max_evs=True
            )
        else:
            # Legacy mode - use base stats directly
            self._calculated_stats = stats

        # HP is set from calculated stats
        self.current_hp = self._calculated_stats.hp
        self.max_hp = self._calculated_stats.hp

        self.status = Status.NONE
        self.sleep_counter = 0

        # Stat stages: -6 to +6 for each stat
        self.stat_stages = {
            StatType.ATTACK: 0,
            StatType.DEFENSE: 0,
            StatType.SPECIAL: 0,
            StatType.SPEED: 0,
            StatType.ACCURACY: 0,
            StatType.EVASION: 0
        }

        # Confusion tracking
        self.confusion_turns = 0

        # Battle state effects
        self.is_seeded = False          # Leech Seed active
        self.has_reflect = False        # Reflect screen active
        self.reflect_turns = 0
        self.has_light_screen = False   # Light Screen active
        self.light_screen_turns = 0
        self.has_mist = False           # Mist active (prevents stat drops)
        self.mist_turns = 0
        self.focus_energy = False       # Focus Energy active (crit boost)
        self.substitute_hp = 0          # Substitute HP (0 = no substitute)
        self.disabled_move = None       # Name of disabled move
        self.disable_turns = 0
        self.last_move_used = None      # For Mirror Move
        self.last_damage_taken = 0      # For Counter
        self.last_damage_physical = False  # Was last damage physical?
        self.last_damage_move_type = None  # Type of last damaging move received (for Counter)

        # Two-turn move states
        self.is_charging = False        # Charging a two-turn move
        self.charging_move = None       # Move being charged
        self.must_recharge = False      # Must recharge (Hyper Beam)
        self.is_semi_invulnerable = False  # Dig/Fly invulnerability

        # Multi-turn move states
        self.multi_turn_move = None     # Current multi-turn move (Thrash, etc.)
        self.multi_turn_counter = 0     # Turns remaining

        # Rage state
        self.is_raging = False          # Currently using Rage

        # Trapping state
        self.is_trapped = False         # Being trapped by Wrap, etc.
        self.trap_turns = 0             # Turns remaining in trap
        self.trapped_by = None          # Pokemon trapping this one

    @property
    def base_stats(self) -> Stats:
        """
        Return calculated stats for battle use.

        This property maintains backwards compatibility - all existing battle code
        accesses pokemon.base_stats and will now get calculated stats instead of
        raw base stats.
        """
        return self._calculated_stats

    @property
    def species_base_stats(self) -> Stats:
        """Return the species' original base stats (for display/reference)."""
        return self._species_base_stats

    def recalculate_stats(self):
        """
        Recalculate stats based on current level/IVs/EVs.

        Call this after level changes (e.g., level-up in RPG mode).
        Preserves current HP percentage.
        """
        if not self._use_calculated_stats:
            return  # Legacy mode - nothing to recalculate

        from engine.stat_calculator import calculate_stats

        # Preserve HP percentage
        hp_percent = self.current_hp / self.max_hp if self.max_hp > 0 else 1.0

        # Recalculate stats
        self._calculated_stats = calculate_stats(
            self._species_base_stats, self.ivs, self.level, self.evs, use_max_evs=True
        )

        # Update HP, preserving percentage
        self.max_hp = self._calculated_stats.hp
        self.current_hp = max(1, int(self.max_hp * hp_percent))

    def is_alive(self) -> bool:
        return self.current_hp > 0

    def take_damage(self, damage: int):
        self.current_hp = max(0, self.current_hp - damage)

    def apply_status(self, status: Status) -> bool:
        """Aplica un estado. Retorna True si fue exitoso"""
        if self.status == Status.NONE:
            self.status = status
            if status == Status.SLEEP:
                self.sleep_counter = random.randint(1, 7)
            elif status == Status.CONFUSION:
                self.confusion_turns = random.randint(1, 4)  # Gen1: 1-4 turns
            return True
        return False

    def modify_stat_stage(self, stat: StatType, stages: int) -> tuple[int, bool]:
        """
        Modifies a stat stage by the given amount.
        Returns: (actual_change, hit_limit)
        """
        old_stage = self.stat_stages[stat]
        new_stage = max(-6, min(6, old_stage + stages))
        actual_change = new_stage - old_stage
        hit_limit = (actual_change != stages)
        self.stat_stages[stat] = new_stage
        return actual_change, hit_limit

    def reset_stat_stages(self):
        """Resets all stat stages to 0"""
        for stat in self.stat_stages:
            self.stat_stages[stat] = 0

    def reset_battle_effects(self):
        """Resets all volatile battle effects (called when switching out)"""
        self.confusion_turns = 0
        self.is_seeded = False
        self.has_reflect = False
        self.reflect_turns = 0
        self.has_light_screen = False
        self.light_screen_turns = 0
        self.has_mist = False
        self.mist_turns = 0
        self.focus_energy = False
        self.substitute_hp = 0
        self.disabled_move = None
        self.disable_turns = 0
        self.last_move_used = None
        self.last_damage_taken = 0
        self.last_damage_physical = False
        self.last_damage_move_type = None
        # Two-turn move states
        self.is_charging = False
        self.charging_move = None
        self.must_recharge = False
        self.is_semi_invulnerable = False
        # Multi-turn move states
        self.multi_turn_move = None
        self.multi_turn_counter = 0
        # Rage state
        self.is_raging = False
        # Trapping state
        self.is_trapped = False
        self.trap_turns = 0
        self.trapped_by = None
        self.reset_stat_stages()

    def is_confused(self) -> bool:
        """Check if Pokemon is confused"""
        return self.confusion_turns > 0

    def get_hp_percentage(self) -> float:
        return (self.current_hp / self.max_hp) * 100

    def get_health_bar(self) -> str:
        """Returns a colored health bar display"""
        from engine.display import create_health_bar
        return create_health_bar(self.current_hp, self.max_hp)
