from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase

class Assistant(ModelBase):
    __tablename__ = 'assistants'
    assistant_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    system_prompt = Column(Text)
    user_prompt = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.now(), nullable=False)

    messages = relationship("AssistantMessage", back_populates="assistant")


