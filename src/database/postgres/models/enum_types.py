import enum


class UserStatusEnum(enum.Enum):
    FREE = "FREE" # пользователь который не в иследовании
    WAIT = "WAIT" # Пользователь в ислодоавнии но не начат
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class ResearchStatusEnum(enum.Enum):

    WAIT = "WAIT"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    PAUSE = "PAUSE"
    ABORTED = "ABORTED"

