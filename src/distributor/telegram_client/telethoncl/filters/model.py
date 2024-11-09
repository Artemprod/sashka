from enum import Enum


class SourceType(str, Enum):
    USER = "user"
    PRIVATE_CHAT = "chat"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
    BOT = "bot"
    ANY = "any"
