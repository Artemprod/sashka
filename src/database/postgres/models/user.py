from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase


class User(ModelBase):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    second_name = Column(String)
    phone_number = Column(String)
    tg_user_id = Column(String)
    friend_bot_data = Column(String)
    tg_link = Column(String)
    is_verified = Column(Boolean)
    is_voice = Column(Boolean)
    is_photo = Column(Boolean)
    is_video = Column(Boolean)
    last_online_date = Column(DateTime)
    language_code = Column(String)

    statuses = relationship("UserStatus", back_populates="user")
    researches = relationship("UserResearch", back_populates="user")
    messages = relationship("UserMessage", back_populates="user")


