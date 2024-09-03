import enum


class UserStatusEnum(enum.Enum):
    FREE = 0 # пользователь который не в иследовании
    WAIT = 1 # Пользователь в ислодоавнии но не начат
    IN_PROGRESS = 2
    DONE = 3


class ResearchStatusEnum(enum.Enum):

    WAIT = 0
    IN_PROGRESS = 1
    DONE = 2
    PAUSE = 3
    ABORTED = 4

