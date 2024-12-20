from enum import Enum

# inheriting from string alows proper serialization for asdict
# https://stackoverflow.com/questions/61338539/how-to-use-enum-value-in-asdict-function-from-dataclasses-module
class GameRender(str,Enum):
    HS =            "honey select"
    HS2 =           "honey select 2"
    DAZ =           "daz"
    KOIKATSU =      "koikatsu"
    HAND_DRAWN =    "hand drawn"
    VAM =           "vam"
    AI =            "ai"
    TK17 =          "tk17"
    UNKNOWN =       "unknown"