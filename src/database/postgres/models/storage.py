from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase


class S3VoiceStorage(ModelBase):
    __tablename__ = 's3_voice_storage'
    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String)
    file_name = Column(String)
    date = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    voice_messages_id = Column(Integer, ForeignKey('voice_messages.voice_message_id'))

    voice_message = relationship("VoiceMessage", back_populates="storage")