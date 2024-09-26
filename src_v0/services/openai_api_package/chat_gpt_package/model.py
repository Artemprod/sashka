from dataclasses import dataclass, field
from enum import Enum
from typing import Union


@dataclass
class GPTOptions:
    api_key: str = field(repr=False)
    model_name: str
    max_message_count: Union[int, None]
    temperature: float
    max_return_tokens: int


class GPTRole(str, Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"


@dataclass
class GPTMessage:
    role: GPTRole
    content: str
