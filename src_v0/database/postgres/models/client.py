from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src_v0.database.postgres.models.base import ModelBase, intpk, str_1024, created_at, str_2048, str_10


class TelegramClient(ModelBase):
    __tablename__ = "telegram_clients"

    client_id: Mapped[intpk]
    telegram_client_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    api_id: Mapped[str] = mapped_column(nullable=False)
    api_hash: Mapped[str] = mapped_column(nullable=False)
    app_version: Mapped[str] = mapped_column(nullable=False)
    device_model: Mapped[str] = mapped_column(nullable=False)
    system_version: Mapped[str] = mapped_column(nullable=False)
    lang_code: Mapped[str_10] = mapped_column(nullable=True)
    test_mode: Mapped[bool] = mapped_column(nullable=False, default=False)
    session_string: Mapped[str_2048] = mapped_column(nullable=True)  # увеличено до 2048
    phone_number: Mapped[str] = mapped_column(nullable=True)
    password: Mapped[str_1024] = mapped_column(nullable=True)
    parse_mode: Mapped[str] = mapped_column(nullable=True, default='HTML')
    workdir: Mapped[str_1024] = mapped_column(nullable=True)  # увеличено до 1024
    created_at: Mapped[created_at]

    messages:Mapped[list["AssistantMessage"]] = relationship(
        back_populates="telegram_client")

    researches:Mapped[list["Research"]] = relationship(
        back_populates="telegram_client"
    )


    def __repr__(self):
        return f"<Client {self.name}>"
