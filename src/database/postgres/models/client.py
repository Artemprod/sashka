from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean

from src.database.postgres.models.base import ModelBase


class Client(ModelBase):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    api_id = Column(String(255), nullable=False)
    api_hash = Column(String(255), nullable=False)
    app_version = Column(String(255), nullable=True)
    device_model = Column(String(255), nullable=True)
    system_version = Column(String(255), nullable=True)
    lang_code = Column(String(5), nullable=True)
    test_mode = Column(Boolean, nullable=True, default=False)
    session_string = Column(String(2048), nullable=True)  # увеличено до 2048
    phone_number = Column(String(255), nullable=True)  # увеличено до 255
    password = Column(String(1024), nullable=True)  # увеличено до 1024
    parse_mode = Column(String(50), nullable=True, default='HTML')
    workdir = Column(String(1024), nullable=True)  # увеличено до 1024
    created_at = Column(TIMESTAMP, default=datetime.now(), nullable=False)

    def __repr__(self):
        return f"<Client {self.name}>"