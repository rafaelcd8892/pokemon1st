"""Team battle engine for multi-Pokemon battles"""

import random
from typing import Optional, Callable

from logging_config import get_logger

logger = get_logger(__name__)

from models.team import Team
from models.pokemon import Pokemon
from models.move import Move
from models.enums import BattleFormat, Status
from engine.battle import execute_turn, determine_turn_order, apply_end_of_turn_effects
from engine.display import format_pokemon_status
from engine.stat_modifiers import get_modified_speed


class BattleAction:
    """Represents a battle action (attack or switch)"""

    def __init__(self, action_type: str, move: Optional[Move] = None,
                 switch_index: Optional[int] = None):
        """
        Args:
            action_type: "attack" or "switch"
            move: The move to use (if attacking)
            switch_index: Index of Pokemon to switch to (if switching)
        """
        self.action_type = action_type
        self.move = move
        self.switch_index = switch_index

    @classmethod
    def attack(cls, move: Move) -> 'BattleAction':
        return cls("attack", move=move)

    @classmethod
    def switch(cls, index: int) -> 'BattleAction':
        return cls("switch", switch_index=index)

    def is_switch(self) -> bool:
        return self.action_type == "switch"

    def __repr__(self) -> str:
        if self.action_type == "attack":
            return f"BattleAction(attack: {self.move.name if self.move else 'None'})"
        return f"BattleAction(switch: {self.switch_index})"


class TeamBattle:
    """
    Manages a battle between two teams.

    Handles:
    - Turn order including switches
    - Forced switches when Pokemon faint
    - Win conditions
    - Battle state tracking
    """

    def __init__(self, team1: Team, team2: Team,
                 battle_format: BattleFormat = BattleFormat.FULL,
                 max_turns: int = 100):
        """
        Initialize a team battle.

        Args:
            team1: Player 1's team
            team2: Player 2's team
            battle_format: The battle format (1v1, 3v3, 6v6)
            max_turns: Maximum number of turns before draw
        """
        self.team1 = team1
        self.team2 = team2
        self.battle_format = battle_format
        self.max_turns = max_turns
        self.turn_count = 0
        self.battle_log: list[str] = []

        # Validate team sizes
        if team1.size > battle_format.team_size:
            raise ValueError(f"Team 1 has {team1.size} Pokemon but format only allows {battle_format.team_size}")
        if team2.size > battle_format.team_size:
            raise ValueError(f"Team 2 has {team2.size} Pokemon but format only allows {battle_format.team_size}")

    def log(self, message: str):
        """Add a message to the battle log and print it"""
        self.battle_log.append(message)
        print(message)

    def display_team_status(self, team: Team, full: bool = False):
        """Display the status of a team's Pokemon"""
        if full:
            self.log(f"\n{team.name}'s Team:")
            for i, info in enumerate(team.get_pokemon_status_list()):
                active_marker = "►" if info['is_active'] else " "
                status_marker = f" [{info['status'].value}]" if info['status'] != Status.NONE else ""
                if info['is_alive']:
                    hp_bar = self._create_mini_hp_bar(info['hp'], info['max_hp'])
                    self.log(f"  {active_marker} {info['name']}: {hp_bar} {info['hp']}/{info['max_hp']}{status_marker}")
                else:
                    self.log(f"  {active_marker} {info['name']}: FAINTED")
        else:
            active = team.active_pokemon
            self.log(format_pokemon_status(active))

    def _create_mini_hp_bar(self, current: int, max_hp: int, width: int = 10) -> str:
        """Create a simple HP bar"""
        percentage = current / max_hp
        filled = int(percentage * width)
        empty = width - filled

        if percentage > 0.5:
            color = "█"
        elif percentage > 0.2:
            color = "▓"
        else:
            color = "░"

        return f"[{color * filled}{'─' * empty}]"

    def get_turn_order(self, action1: BattleAction, action2: BattleAction) -> list[tuple[Team, BattleAction, Team]]:
        """
        Determine the order of actions for this turn.

        Switches always happen before attacks.
        Between two attacks, faster Pokemon goes first.

        Returns:
            List of (acting_team, action, opponent_team) tuples in order
        """
        # Switches always go first
        if action1.is_switch() and not action2.is_switch():
            return [(self.team1, action1, self.team2), (self.team2, action2, self.team1)]
        if action2.is_switch() and not action1.is_switch():
            return [(self.team2, action2, self.team1), (self.team1, action1, self.team2)]

        # Both switching - order doesn't matter for switches
        if action1.is_switch() and action2.is_switch():
            return [(self.team1, action1, self.team2), (self.team2, action2, self.team1)]

        # Both attacking - use speed to determine order
        pokemon1 = self.team1.active_pokemon
        pokemon2 = self.team2.active_pokemon

        first, second = determine_turn_order(pokemon1, pokemon2)

        if first == pokemon1:
            return [(self.team1, action1, self.team2), (self.team2, action2, self.team1)]
        else:
            return [(self.team2, action2, self.team1), (self.team1, action1, self.team2)]

    def execute_action(self, acting_team: Team, action: BattleAction, opponent_team: Team) -> bool:
        """
        Execute a single action.

        Args:
            acting_team: The team taking the action
            action: The action to take
            opponent_team: The opposing team

        Returns:
            True if the action was executed, False if it couldn't be
        """
        if action.is_switch():
            old_pokemon = acting_team.active_pokemon
            if acting_team.switch_pokemon(action.switch_index):
                new_pokemon = acting_team.active_pokemon
                self.log(f"\n{acting_team.name} retira a {old_pokemon.name}!")
                self.log(f"¡Adelante, {new_pokemon.name}!")
                self.log(format_pokemon_status(new_pokemon))
                return True
            return False
        else:
            # Attack
            attacker = acting_team.active_pokemon
            defender = opponent_team.active_pokemon

            if not attacker.is_alive():
                return False

            execute_turn(attacker, defender, action.move)
            return True

    def execute_turn_pair(self, action1: BattleAction, action2: BattleAction) -> Optional[Team]:
        """
        Execute a full turn with both players' actions.

        Args:
            action1: Team 1's action
            action2: Team 2's action

        Returns:
            The winning team if battle ended, None otherwise
        """
        self.turn_count += 1
        self.log(f"\n{'═' * 40}")
        self.log(f"--- Turno {self.turn_count} ---")
        self.log(f"{'═' * 40}")

        # Get turn order
        action_order = self.get_turn_order(action1, action2)

        # Execute actions in order
        for acting_team, action, opponent_team in action_order:
            # Skip if acting Pokemon fainted from previous action
            if not acting_team.active_pokemon.is_alive():
                continue

            self.execute_action(acting_team, action, opponent_team)

            # Check if defender fainted
            defender_team = opponent_team
            if not defender_team.active_pokemon.is_alive():
                self.log(f"\n¡{defender_team.active_pokemon.name} se debilitó!")

                # Check for win condition
                if defender_team.is_defeated():
                    return acting_team

                # Force switch for the defeated Pokemon's team
                self.log(f"\n{defender_team.name} debe elegir otro Pokémon...")

        # Apply end of turn effects
        apply_end_of_turn_effects(self.team1.active_pokemon, self.team2.active_pokemon)

        # Check for fainting from end-of-turn effects
        for team in [self.team1, self.team2]:
            if not team.active_pokemon.is_alive():
                self.log(f"\n¡{team.active_pokemon.name} se debilitó!")
                if team.is_defeated():
                    other_team = self.team2 if team == self.team1 else self.team1
                    return other_team

        return None

    def check_winner(self) -> Optional[Team]:
        """Check if either team has won"""
        if self.team1.is_defeated():
            return self.team2
        if self.team2.is_defeated():
            return self.team1
        if self.turn_count >= self.max_turns:
            # Draw - return None but battle should end
            return None
        return None

    def needs_forced_switch(self, team: Team) -> bool:
        """Check if a team needs to make a forced switch"""
        return not team.active_pokemon.is_alive() and not team.is_defeated()

    def run_battle(self,
                   get_player_action: Callable[[Team, Team], BattleAction],
                   get_opponent_action: Callable[[Team, Team], BattleAction],
                   get_forced_switch: Optional[Callable[[Team], int]] = None) -> Optional[Team]:
        """
        Run the full battle loop.

        Args:
            get_player_action: Function to get player's action (team, opponent) -> action
            get_opponent_action: Function to get opponent's action (team, opponent) -> action
            get_forced_switch: Optional function to handle forced switches (team) -> index

        Returns:
            The winning team, or None for a draw
        """
        self.log("═" * 50)
        self.log("         ¡COMIENZA LA BATALLA!")
        self.log(f"         Formato: {self.battle_format.description}")
        self.log("═" * 50)

        self.log(f"\n{self.team1.name}: ¡Adelante, {self.team1.active_pokemon.name}!")
        self.display_team_status(self.team1)

        self.log(f"\n{self.team2.name}: ¡Adelante, {self.team2.active_pokemon.name}!")
        self.display_team_status(self.team2)

        while True:
            # Check win condition
            winner = self.check_winner()
            if winner:
                self.log("\n" + "═" * 50)
                self.log(f"¡{winner.name} gana la batalla!")
                self.log("═" * 50)
                return winner

            if self.turn_count >= self.max_turns:
                self.log("\n" + "═" * 50)
                self.log("¡La batalla terminó en empate por límite de turnos!")
                self.log("═" * 50)
                return None

            # Handle forced switches first
            for team, get_action in [(self.team1, get_forced_switch), (self.team2, get_forced_switch)]:
                if self.needs_forced_switch(team) and get_action:
                    switch_idx = get_action(team)
                    if switch_idx is not None:
                        team.switch_pokemon(switch_idx)
                        self.log(f"\n{team.name} envía a {team.active_pokemon.name}!")
                        self.display_team_status(team)

            # Get actions from both players
            action1 = get_player_action(self.team1, self.team2)
            action2 = get_opponent_action(self.team2, self.team1)

            # Execute the turn
            winner = self.execute_turn_pair(action1, action2)
            if winner:
                self.log("\n" + "═" * 50)
                self.log(f"¡{winner.name} gana la batalla!")
                self.log("═" * 50)
                return winner

            # Show team status at end of turn
            self.log("\n--- Estado de los equipos ---")
            self.display_team_status(self.team1, full=True)
            self.display_team_status(self.team2, full=True)


def create_random_team(size: int, trainer_name: str = "Trainer") -> Team:
    """
    Create a random team of Pokemon.

    Args:
        size: Number of Pokemon (1-6)
        trainer_name: Name for the trainer

    Returns:
        A Team with random Pokemon
    """
    from data.data_loader import (
        get_kanto_pokemon_list,
        get_pokemon_data,
        get_pokemon_moves_gen1,
        create_move
    )
    from models.stats import Stats
    from models.enums import Type

    kanto_list = get_kanto_pokemon_list()
    selected_names = random.sample(kanto_list, min(size, len(kanto_list)))

    pokemon_list = []
    for name in selected_names:
        poke_data = get_pokemon_data(name)
        moves_gen1 = get_pokemon_moves_gen1(name)
        moves_selected = random.sample(moves_gen1, min(4, len(moves_gen1)))
        moves = [create_move(m) for m in moves_selected]

        stats = Stats(
            hp=poke_data['stats'].get('hp', 100),
            attack=poke_data['stats'].get('attack', 50),
            defense=poke_data['stats'].get('defense', 50),
            special=poke_data['stats'].get('special-attack', 50),
            speed=poke_data['stats'].get('speed', 50)
        )
        types = [getattr(Type, t.upper(), Type.NORMAL) for t in poke_data['types']]

        pokemon = Pokemon(poke_data['name'], types, stats, moves, level=50)
        pokemon_list.append(pokemon)

        logger.debug(f"Created {name} with moves: {[m.name for m in moves]}")

    return Team(pokemon_list, trainer_name)


def get_random_ai_action(team: Team, opponent_team: Team) -> BattleAction:
    """
    Simple AI that picks a random move or occasionally switches.

    Args:
        team: The AI's team
        opponent_team: The opponent's team

    Returns:
        A BattleAction
    """
    active = team.active_pokemon

    # 10% chance to switch if possible and Pokemon is low on HP
    if team.can_switch() and active.current_hp < active.max_hp * 0.3:
        if random.random() < 0.3:  # 30% chance when low HP
            available = team.get_available_switches()
            switch_idx = random.choice(available)[0]
            logger.debug(f"AI switching to index {switch_idx}")
            return BattleAction.switch(switch_idx)

    # Pick a random move with PP
    available_moves = [m for m in active.moves if m.has_pp()]
    if available_moves:
        move = random.choice(available_moves)
        return BattleAction.attack(move)

    # No moves with PP - use Struggle (first move as placeholder)
    return BattleAction.attack(active.moves[0])


def get_random_forced_switch(team: Team) -> Optional[int]:
    """
    Handle forced switch by picking a random available Pokemon.

    Args:
        team: The team that needs to switch

    Returns:
        Index of Pokemon to switch to, or None if no switch possible
    """
    available = team.get_available_switches()
    if available:
        return random.choice(available)[0]
    return None
