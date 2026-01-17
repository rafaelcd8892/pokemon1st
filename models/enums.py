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

class MoveCategory(Enum):
    PHYSICAL = "Physical"
    SPECIAL = "Special"
    STATUS = "Status"