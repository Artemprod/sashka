from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk, str_1024, created_at, str_2048, str_10


class S3VoiceStorage(ModelBase):
    __tablename__ = 's3_voice_storage'
    id: Mapped[intpk]
    path: Mapped[str_1024]
    file_name: Mapped[str_1024]
    created_at: Mapped[created_at]

    voice_messages_id: Mapped[int] = mapped_column(ForeignKey('voice_messages.voice_message_id'))
    voice_message:Mapped["VoiceMessage"] = relationship(back_populates="storage")
