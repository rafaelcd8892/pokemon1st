from enum import Enum

class Type(Enum):
    NORMAL = "Normal"
    FIRE = "Fire"
    WATER = "Water"
    ELECTRIC = "Electric"
    GRASS = "Grass"
    ICE = "Ice"
    FIGHTING = "Fighting"
    POISON = "Poison"
    GROUND = "Ground"
    FLYING = "Flying"
    PSYCHIC = "Psychic"
    BUG = "Bug"
    ROCK = "Rock"
    GHOST = "Ghost"
    DRAGON = "Dragon"

class Status(Enum):
    NONE = "None"
    BURN = "Burn"
    FREEZE = "Freeze"
    PARALYSIS = "Paralysis"
    POISON = "Poison"
    SLEEP = "Sleep"
    CONFUSION = "Confusion"

class MoveCategory(Enum):
    PHYSICAL = "Physical"
    SPECIAL = "Special"
    STATUS = "Status"

class StatType(Enum):
    """Stats that can be modified by stat stages"""
    ATTACK = "Attack"
    DEFENSE = "Defense"
    SPECIAL = "Special"
    SPEED = "Speed"
    ACCURACY = "Accuracy"
    EVASION = "Evasion"


class BattleFormat(Enum):
    """Battle format options"""
    SINGLE = (1, "1v1 Single Battle")
    TRIPLE = (3, "3v3 Battle")
    FULL = (6, "6v6 Full Battle")

    def __init__(self, team_size: int, description: str):
        self.team_size = team_size
        self.description = description