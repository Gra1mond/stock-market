from enum import Enum


class GameState(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class FinishReason(str, Enum):
    NOT_ENOUGH_PLAYERS = "not_enough_players"
    ROUNDS_COMPLETED = "rounds_completed"
    FORCED_BY_PLAYER = "forced_by_player"