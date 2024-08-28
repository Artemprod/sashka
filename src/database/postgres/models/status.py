from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase




class UserStatus(ModelBase):
    __tablename__ = 'user_status'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime)
    status_id = Column(Integer, ForeignKey('var_status_name.status_id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))

    status = relationship("VarStatusName")
    user = relationship("User", back_populates="statuses")


class UserStatusName(ModelBase):
    __tablename__ = 'user_status_name'
    status_id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String)




class ResearchStatusName(ModelBase):
    __tablename__ = 'research_status_name'
    status_id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String)
