"""
Battle rulesets and cups for Pokemon Gen 1.

Defines rules and restrictions for different battle formats,
inspired by Pokemon Stadium cups (Poke Cup, Prime Cup, etc.).
"""

from dataclasses import dataclass, field
from typing import Optional, Set, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from models.pokemon import Pokemon


class CupType(Enum):
    """Predefined cup types based on Pokemon Stadium."""
    STANDARD = "standard"       # Level 50, no restrictions
    POKE_CUP = "poke_cup"       # Level 50-55, sum <= 155, no Mew/Mewtwo
    PRIME_CUP = "prime_cup"     # Level 100, no restrictions
    LITTLE_CUP = "little_cup"   # Level 5, basic Pokemon only
    PIKA_CUP = "pika_cup"       # Level 15-20, basic Pokemon only
    PETIT_CUP = "petit_cup"     # Level 25-30, height/weight restrictions
    CUSTOM = "custom"           # User-defined rules


# Pokemon that can evolve (basic/first stage Pokemon)
# Used for cups that restrict to "basic Pokemon only"
BASIC_POKEMON = {
    "bulbasaur", "charmander", "squirtle", "caterpie", "weedle",
    "pidgey", "rattata", "spearow", "ekans", "pikachu", "sandshrew",
    "nidoran-f", "nidoran-m", "clefairy", "vulpix", "jigglypuff",
    "zubat", "oddish", "paras", "venonat", "diglett", "meowth",
    "psyduck", "mankey", "growlithe", "poliwag", "abra", "machop",
    "bellsprout", "tentacool", "geodude", "ponyta", "slowpoke",
    "magnemite", "doduo", "seel", "grimer", "shellder", "gastly",
    "drowzee", "krabby", "voltorb", "exeggcute", "cubone", "koffing",
    "rhyhorn", "horsea", "goldeen", "staryu", "magikarp", "eevee",
    "porygon", "omanyte", "kabuto", "dratini",
    # Single-stage Pokemon (no evolution)
    "farfetchd", "kangaskhan", "mr-mime", "scyther", "jynx",
    "electabuzz", "magmar", "pinsir", "tauros", "lapras", "ditto",
    "aerodactyl", "snorlax",
}

# Legendary Pokemon
LEGENDARY_POKEMON = {"articuno", "zapdos", "moltres", "mewtwo", "mew"}


@dataclass
class Ruleset:
    """
    Defines rules and restrictions for a battle format.

    Attributes:
        name: Display name for the ruleset
        cup_type: Type of cup/format
        min_level: Minimum Pokemon level allowed
        max_level: Maximum Pokemon level allowed
        default_level: Default level for Pokemon in this format
        level_sum_limit: Maximum sum of all Pokemon levels (optional)
        min_team_size: Minimum Pokemon per team
        max_team_size: Maximum Pokemon per team
        banned_pokemon: Set of Pokemon names that cannot be used
        allowed_pokemon: If set, only these Pokemon are allowed
        basic_pokemon_only: If True, only unevolved Pokemon allowed
        allow_legendaries: If False, legendary Pokemon are banned
        perfect_ivs: If True, use perfect IVs; if False, random IVs
        max_evs: If True, use max EVs; if False, use zero EVs
        use_calculated_stats: If True, use Gen 1 stat formula
    """
    name: str
    cup_type: CupType = CupType.STANDARD

    # Level restrictions
    min_level: int = 1
    max_level: int = 100
    default_level: int = 50
    level_sum_limit: Optional[int] = None

    # Team restrictions
    min_team_size: int = 1
    max_team_size: int = 6

    # Pokemon restrictions
    banned_pokemon: Set[str] = field(default_factory=set)
    allowed_pokemon: Optional[Set[str]] = None
    basic_pokemon_only: bool = False
    allow_legendaries: bool = True

    # Stat calculation settings
    perfect_ivs: bool = True
    max_evs: bool = True
    use_calculated_stats: bool = True

    def validate_pokemon(self, pokemon: 'Pokemon') -> tuple[bool, str]:
        """
        Validate a single Pokemon against this ruleset.

        Args:
            pokemon: The Pokemon to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        name_lower = pokemon.name.lower()

        # Check banned Pokemon
        if name_lower in {p.lower() for p in self.banned_pokemon}:
            return False, f"{pokemon.name} is banned in {self.name}"

        # Check allowed Pokemon (whitelist)
        if self.allowed_pokemon is not None:
            if name_lower not in {p.lower() for p in self.allowed_pokemon}:
                return False, f"{pokemon.name} is not allowed in {self.name}"

        # Check basic Pokemon restriction
        if self.basic_pokemon_only:
            if name_lower not in BASIC_POKEMON:
                return False, f"{pokemon.name} is not a basic Pokemon (required for {self.name})"

        # Check legendary restriction
        if not self.allow_legendaries:
            if name_lower in LEGENDARY_POKEMON:
                return False, f"{pokemon.name} is a legendary Pokemon (not allowed in {self.name})"

        # Check level range
        if pokemon.level < self.min_level:
            return False, f"{pokemon.name} (Lv.{pokemon.level}) is below minimum level {self.min_level}"

        if pokemon.level > self.max_level:
            return False, f"{pokemon.name} (Lv.{pokemon.level}) exceeds maximum level {self.max_level}"

        return True, ""

    def validate_team(self, pokemon_list: list) -> tuple[bool, str]:
        """
        Validate an entire team against this ruleset.

        Args:
            pokemon_list: List of Pokemon to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check team size
        if len(pokemon_list) < self.min_team_size:
            return False, f"Team needs at least {self.min_team_size} Pokemon"

        if len(pokemon_list) > self.max_team_size:
            return False, f"Team cannot exceed {self.max_team_size} Pokemon"

        # Check level sum limit
        if self.level_sum_limit is not None:
            level_sum = sum(p.level for p in pokemon_list)
            if level_sum > self.level_sum_limit:
                return False, f"Team level sum ({level_sum}) exceeds limit ({self.level_sum_limit})"

        # Validate each Pokemon
        for pokemon in pokemon_list:
            valid, msg = self.validate_pokemon(pokemon)
            if not valid:
                return False, msg

        # Check for duplicate Pokemon
        names = [p.name.lower() for p in pokemon_list]
        if len(names) != len(set(names)):
            return False, "Team cannot have duplicate Pokemon"

        return True, ""

    def get_description(self) -> str:
        """Get a human-readable description of the ruleset."""
        parts = [f"{self.name}"]

        if self.min_level == self.max_level:
            parts.append(f"Level {self.default_level}")
        else:
            parts.append(f"Level {self.min_level}-{self.max_level}")

        if self.level_sum_limit:
            parts.append(f"Sum \u2264 {self.level_sum_limit}")

        if self.max_team_size < 6:
            parts.append(f"{self.max_team_size}v{self.max_team_size}")

        if self.basic_pokemon_only:
            parts.append("Basic only")

        if not self.allow_legendaries:
            parts.append("No legendaries")

        return " | ".join(parts)


# =============================================================================
# Predefined Rulesets (Pokemon Stadium-style)
# =============================================================================

STANDARD_RULES = Ruleset(
    name="Standard",
    cup_type=CupType.STANDARD,
    default_level=50,
    max_level=100,
)

POKE_CUP_RULES = Ruleset(
    name="Poke Cup",
    cup_type=CupType.POKE_CUP,
    min_level=50,
    max_level=55,
    default_level=50,
    level_sum_limit=155,
    max_team_size=3,
    banned_pokemon={"mew", "mewtwo"},
    allow_legendaries=False,
)

PRIME_CUP_RULES = Ruleset(
    name="Prime Cup",
    cup_type=CupType.PRIME_CUP,
    min_level=1,
    max_level=100,
    default_level=100,
    max_team_size=3,
)

LITTLE_CUP_RULES = Ruleset(
    name="Little Cup",
    cup_type=CupType.LITTLE_CUP,
    min_level=5,
    max_level=5,
    default_level=5,
    max_team_size=3,
    basic_pokemon_only=True,
    allow_legendaries=False,
)

PIKA_CUP_RULES = Ruleset(
    name="Pika Cup",
    cup_type=CupType.PIKA_CUP,
    min_level=15,
    max_level=20,
    default_level=15,
    level_sum_limit=50,
    max_team_size=3,
    basic_pokemon_only=True,
    allow_legendaries=False,
)

PETIT_CUP_RULES = Ruleset(
    name="Petit Cup",
    cup_type=CupType.PETIT_CUP,
    min_level=25,
    max_level=30,
    default_level=25,
    level_sum_limit=80,
    max_team_size=3,
    allow_legendaries=False,
)

# Full team variants (6v6)
STANDARD_6V6_RULES = Ruleset(
    name="Standard 6v6",
    cup_type=CupType.STANDARD,
    default_level=50,
    max_level=100,
    max_team_size=6,
)

PRIME_CUP_6V6_RULES = Ruleset(
    name="Prime Cup 6v6",
    cup_type=CupType.PRIME_CUP,
    default_level=100,
    max_level=100,
    max_team_size=6,
)

# Collection of all predefined rulesets
ALL_RULESETS = [
    STANDARD_RULES,
    POKE_CUP_RULES,
    PRIME_CUP_RULES,
    LITTLE_CUP_RULES,
    PIKA_CUP_RULES,
    PETIT_CUP_RULES,
    STANDARD_6V6_RULES,
    PRIME_CUP_6V6_RULES,
]


def get_ruleset_by_name(name: str) -> Optional[Ruleset]:
    """Get a predefined ruleset by name."""
    for ruleset in ALL_RULESETS:
        if ruleset.name.lower() == name.lower():
            return ruleset
    return None
