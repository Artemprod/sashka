from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase


class UserMessage(ModelBase):
    __tablename__ = 'user_messages'
    user_message_id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_1 = Column(Integer, ForeignKey('users.user_id'))
    date = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    chat = Column(Integer)
    forwarded_from = Column(String)
    reply_to_message_id = Column(Integer)
    mentioned = Column(Boolean)
    media = Column(Boolean)
    edit_date = Column(DateTime)
    voice = Column(Boolean)
    text = Column(Text)

    user = relationship("User", back_populates="messages")
    voice_messages = relationship("VoiceMessage", back_populates="user_message")


class VoiceMessage(ModelBase):
    __tablename__ = 'voice_messages'
    voice_message_id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String)
    file_unique_id = Column(String)
    duration = Column(Integer)
    mime_type = Column(String)
    file_size = Column(Integer)
    date = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    user_message_id = Column(Integer, ForeignKey('user_messages.user_message_id'))

    user_message = relationship("UserMessage", back_populates="voice_messages")
    storage = relationship("S3VoiceStorage", back_populates="voice_message")


class AssistantMessage(ModelBase):
    __tablename__ = 'assistant_messages'
    assistant_message_id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text)
    chat_id = Column(Integer)
    to_user_id = Column(Integer)
    date = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    assistant_id = Column(Integer, ForeignKey('assistants.assistant_id'))
    telegram_client_id = Column(Integer, ForeignKey('telegram_clients.telegram_client_id'))

    assistant = relationship("Assistant", back_populates="messages")
    telegram_client = relationship("TelegramClient", back_populates="messages")
