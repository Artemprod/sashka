import datetime
from typing import Annotated

from sqlalchemy import text, Integer, DateTime, String
from sqlalchemy.orm import DeclarativeBase, mapped_column

# ModelBase = declarative_base()

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"),
                                                        onupdate=datetime.datetime.now(datetime.UTC))]
str_2048 = Annotated[str, 2048]
str_1024 = Annotated[str, 1024]
str_10 = Annotated[str, 10]


class ModelBase(DeclarativeBase):

    type_annotation_map = {
        intpk: Integer,
        created_at: DateTime,
        updated_at: DateTime,
        str_2048: String(2048),
        str_1024: String(2048),
        str_10: String(2048),
    }
