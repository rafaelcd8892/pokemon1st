"""Pokemon Team model for multi-Pokemon battles"""

from typing import Optional
from models.pokemon import Pokemon


class Team:
    """
    Represents a trainer's Pokemon team.

    Supports teams of 1-6 Pokemon for different battle formats:
    - 1v1: Single Pokemon
    - 3v3: Three Pokemon
    - 6v6: Full team
    """

    def __init__(self, pokemon: list[Pokemon], name: str = "Trainer"):
        """
        Initialize a team with a list of Pokemon.

        Args:
            pokemon: List of Pokemon (1-6)
            name: Trainer name for display
        """
        if not pokemon or len(pokemon) > 6:
            raise ValueError("Team must have 1-6 Pokemon")

        self._pokemon = pokemon
        self._active_index = 0
        self.name = name

    @property
    def active_pokemon(self) -> Pokemon:
        """Get the currently active Pokemon"""
        return self._pokemon[self._active_index]

    @property
    def pokemon(self) -> list[Pokemon]:
        """Get all Pokemon in the team"""
        return self._pokemon

    @property
    def size(self) -> int:
        """Get the number of Pokemon in the team"""
        return len(self._pokemon)

    def get_alive_pokemon(self) -> list[Pokemon]:
        """Get all Pokemon that are still alive"""
        return [p for p in self._pokemon if p.is_alive()]

    def get_available_switches(self) -> list[tuple[int, Pokemon]]:
        """
        Get Pokemon available to switch to.

        Returns:
            List of (index, Pokemon) tuples for alive, non-active Pokemon
        """
        return [
            (i, p) for i, p in enumerate(self._pokemon)
            if p.is_alive() and i != self._active_index
        ]

    def can_switch(self) -> bool:
        """Check if the trainer can switch Pokemon"""
        return len(self.get_available_switches()) > 0

    def switch_pokemon(self, index: int) -> bool:
        """
        Switch to a different Pokemon.

        Args:
            index: Index of the Pokemon to switch to

        Returns:
            True if switch was successful, False otherwise
        """
        if index < 0 or index >= len(self._pokemon):
            return False

        if index == self._active_index:
            return False

        target = self._pokemon[index]
        if not target.is_alive():
            return False

        # Reset volatile battle effects on the Pokemon being switched out
        current = self.active_pokemon
        current.reset_battle_effects()

        self._active_index = index
        return True

    def force_switch(self) -> bool:
        """
        Force switch to the next available Pokemon (when current faints).

        Returns:
            True if a Pokemon was available to switch to, False if all fainted
        """
        available = self.get_available_switches()
        if available:
            # Switch to the first available Pokemon
            self._active_index = available[0][0]
            return True
        return False

    def is_defeated(self) -> bool:
        """Check if all Pokemon in the team have fainted"""
        return all(not p.is_alive() for p in self._pokemon)

    def get_pokemon_status_list(self) -> list[dict]:
        """
        Get status information for all Pokemon in the team.

        Returns:
            List of dicts with name, hp, max_hp, is_active, is_alive
        """
        return [
            {
                'name': p.name,
                'hp': p.current_hp,
                'max_hp': p.max_hp,
                'is_active': i == self._active_index,
                'is_alive': p.is_alive(),
                'status': p.status
            }
            for i, p in enumerate(self._pokemon)
        ]

    def heal_all(self):
        """Fully heal all Pokemon (used for testing or between battles)"""
        for pokemon in self._pokemon:
            pokemon.current_hp = pokemon.max_hp
            pokemon.status = pokemon.status.__class__.NONE
            pokemon.reset_battle_effects()

    def __repr__(self) -> str:
        alive = len(self.get_alive_pokemon())
        return f"Team({self.name}, {alive}/{self.size} alive, active={self.active_pokemon.name})"
