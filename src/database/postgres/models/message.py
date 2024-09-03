from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk, str_1024, created_at, str_2048, str_10


class UserMessage(ModelBase):
    __tablename__ = 'user_messages'

    user_message_id: Mapped[intpk]
    from_user: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
    chat: Mapped[int]
    forwarded_from: Mapped[Optional[str]]
    reply_to_message_id: Mapped[Optional[int]]
    media: Mapped[bool]
    edit_date: Mapped[Optional[datetime]]
    voice: Mapped[bool]
    text: Mapped[str]
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
        back_populates="voice_message")

    storage: Mapped["S3VoiceStorage"] = relationship(
        back_populates="voice_message")


class AssistantMessage(ModelBase):
    __tablename__ = 'assistant_messages'

    assistant_message_id: Mapped[intpk]
    text: Mapped[str]
    chat_id: Mapped[int]
    created_at: Mapped[created_at]

    to_user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_user_id'))
    assistant_id: Mapped[int] = mapped_column(ForeignKey('assistants.assistant_id'))
    telegram_client_id: Mapped[int] = mapped_column(ForeignKey('telegram_clients.telegram_client_id'))

    to_user: Mapped["User"] = relationship(
        back_populates="assistant_messages"
    )

    assistant: Mapped["Assistant"] = relationship(
        back_populates="messages")

    telegram_client: Mapped["TelegramClient"] = relationship(
        back_populates="messages")


