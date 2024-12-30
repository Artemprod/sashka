from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at
from src.database.postgres.models.base import intpk
from src.database.postgres.models.base import str_1024


class S3VoiceStorage(ModelBase):
    __tablename__ = "s3_voice_storage"

    id: Mapped[intpk]
    path: Mapped[str_1024]
    file_name: Mapped[str_1024]
    created_at: Mapped[created_at]
    voice_messages_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("voice_messages.voice_message_id"))

    voice_message: Mapped["VoiceMessage"] = relationship(back_populates="storage")
