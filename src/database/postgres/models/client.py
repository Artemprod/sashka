
from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at
from src.database.postgres.models.base import intpk
from src.database.postgres.models.base import str_10
from src.database.postgres.models.base import str_1024
from src.database.postgres.models.base import str_2048


class TelegramClient(ModelBase):
    __tablename__ = "telegram_clients"

    client_id: Mapped[intpk]

    telegram_client_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
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

    user_messages:Mapped[list["UserMessage"]] = relationship(
        back_populates="telegram_client")




    def __repr__(self):
        return f"<Client {self.name}>"
