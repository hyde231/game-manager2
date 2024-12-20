from enum import Enum

# inheriting from string alows proper serialization for asdict
# https://stackoverflow.com/questions/61338539/how-to-use-enum-value-in-asdict-function-from-dataclasses-module
class GameEngine(str,Enum):
    ADRIFT =    "adrift"
    FLASH =     "flash"
    HTML =      "html"
    JAVA =      "java"
    OTHER =     "other"
    QSP =       "qsp"
    RAGS =      "rags" #rapid adventure game development system
    RENPY =     "renpy"
    RPGM =      "rpgm"
    TADS =      "tads"
    UNITY =     "unity"
    UNKNOWN =   "unknown"
    UNREAL =    "unreal" #Unreal Engine
    WEBGL =     "webgl"
    WOLFRPG =   "wolf rpg"