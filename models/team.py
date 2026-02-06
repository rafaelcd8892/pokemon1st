"""Team class for managing a group of Pokemon in battle"""

from typing import List, Optional
from models.pokemon import Pokemon
from models.enums import Status


class Team:
    """
    Represents a trainer's team of Pokemon.

    Manages the active Pokemon and switching between team members.
    """

    def __init__(self, pokemon: List[Pokemon], name: str = "Trainer"):
        """
        Initialize a team.

        Args:
            pokemon: List of Pokemon in the team
            name: Team/trainer name
        """
        if not pokemon:
            raise ValueError("Team must have at least one Pokemon")

        self._pokemon = pokemon
        self._name = name
        self._active_index = 0

    @property
    def name(self) -> str:
        """Get the team/trainer name"""
        return self._name

    @property
    def pokemon(self) -> List[Pokemon]:
        """Get the list of all Pokemon in the team"""
        return self._pokemon

    @property
    def size(self) -> int:
        """Get the number of Pokemon in the team"""
        return len(self._pokemon)

    @property
    def active_pokemon(self) -> Pokemon:
        """Get the currently active Pokemon"""
        return self._pokemon[self._active_index]

    @property
    def active_index(self) -> int:
        """Get the index of the currently active Pokemon"""
        return self._active_index

    def get_available_switches(self) -> List[tuple[int, Pokemon]]:
        """
        Get list of Pokemon that can be switched to.

        Returns:
            List of (index, pokemon) tuples for alive, non-active Pokemon
        """
        available = []
        for i, poke in enumerate(self._pokemon):
            if i != self._active_index and poke.is_alive():
                available.append((i, poke))
        return available

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
        if not self._pokemon[index].is_alive():
            return False

        # Clear volatile battle effects on the outgoing Pokemon
        self._pokemon[self._active_index].reset_battle_effects()
        self._active_index = index
        return True

    def get_pokemon_status_list(self) -> List[dict]:
        """
        Get status information for all Pokemon in the team.

        Returns:
            List of dicts with pokemon status info
        """
        status_list = []
        for i, poke in enumerate(self._pokemon):
            status_list.append({
                'index': i,
                'name': poke.name,
                'hp': poke.current_hp,
                'max_hp': poke.max_hp,
                'status': poke.status if hasattr(poke, 'status') else Status.NONE,
                'is_alive': poke.is_alive(),
                'is_active': i == self._active_index
            })
        return status_list

    def has_alive_pokemon(self) -> bool:
        """Check if any Pokemon in the team is still alive"""
        return any(poke.is_alive() for poke in self._pokemon)

    def can_switch(self) -> bool:
        """Check if there are any available Pokemon to switch to"""
        return len(self.get_available_switches()) > 0

    def is_defeated(self) -> bool:
        """Check if the team has been defeated (no alive Pokemon)"""
        return not self.has_alive_pokemon()

    def count_alive(self) -> int:
        """Count how many Pokemon are still alive"""
        return sum(1 for poke in self._pokemon if poke.is_alive())

    def __repr__(self) -> str:
        alive = self.count_alive()
        return f"Team({self._name}, {alive}/{self.size} alive, active: {self.active_pokemon.name})"
