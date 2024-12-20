from enum import Enum

# inheriting from string alows proper serialization for asdict
# https://stackoverflow.com/questions/61338539/how-to-use-enum-value-in-asdict-function-from-dataclasses-module
class GameStatus(str,Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ONHOLD = "onhold"  # aka hiatus
    UNKNOWN = "unknown"