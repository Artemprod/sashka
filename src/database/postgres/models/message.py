from datetime import datetime
from typing import Optional

from sqlalchemy import Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from sqlalchemy.orm import Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk, created_at
from src.database.postgres.models.storage import S3VoiceStorage


class UserMessage(ModelBase):
    __tablename__ = 'user_messages'

    user_message_id: Mapped[intpk]
    from_user: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.tg_user_id'))
    chat: Mapped[int] = mapped_column(BigInteger)
    forwarded_from: Mapped[Optional[str]]
    reply_to_message_id: Mapped[Optional[int]]
    media: Mapped[bool]
    edit_date: Mapped[Optional[datetime]]
    voice: Mapped[bool]
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[created_at]

    user: Mapped["User"] = relationship(
        back_populates="messages")

    voice_message: Mapped["VoiceMessage"] = relationship(
        back_populates="user_message")


class VoiceMessage(ModelBase):
    __tablename__ = 'voice_messages'
    voice_message_id: Mapped[intpk]
    file_id: Mapped[str]
    file_unique_id: Mapped[str]
    duration: Mapped[Optional[int]]
    mime_type: Mapped[Optional[str]]
    file_size: Mapped[Optional[float]]
    created_at: Mapped[created_at]

    user_message_id: Mapped[int] = mapped_column(ForeignKey('user_messages.user_message_id'))

    user_message: Mapped["UserMessage"] = relationship(
        back_populates="voice_message",)

    storage: Mapped["S3VoiceStorage"] = relationship(
        back_populates="voice_message")


class AssistantMessage(ModelBase):
    __tablename__ = 'assistant_messages'

    assistant_message_id: Mapped[intpk]
    text: Mapped[str] = mapped_column(Text)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[created_at]

    to_user_id: Mapped[int] = mapped_column(BigInteger,ForeignKey('users.tg_user_id'))
    assistant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('assistants.assistant_id'))

    telegram_client_id: Mapped[int] = mapped_column(BigInteger,ForeignKey('telegram_clients.client_id'))

    to_user: Mapped["User"] = relationship(
        back_populates="assistant_messages"
    )

    assistant:  Mapped["Assistant"] = relationship("Assistant",
                                                   back_populates="messages")

    telegram_client: Mapped["TelegramClient"] = relationship("TelegramClient",
                                                             back_populates="messages")


