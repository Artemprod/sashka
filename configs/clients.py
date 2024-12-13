import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic import field_validator

from configs.base import BaseConfig
load_dotenv()
sys.path.append(str(Path(__file__).parent.parent))


class TelethonClientContainer(BaseConfig):
    def_mode: bool = Field(
        default=False,
        validation_alias='DEV_MODE'
    )
    shelve_file_path: str = Field(
        default=str(Path(__file__).parent.parent.joinpath("class_container", "telethon.db")),
        validation_alias='TELETHON_CONTAINER_SHELVE_PATH'
    )

    @field_validator("def_mode",
                     mode='before')
    def split_str(cls, field_data):
        if isinstance(field_data, str):
            return "true" == field_data.lower()
        return field_data

    @field_validator("shelve_file_path", mode="before")
    def ensure_directory_exists(cls, field_data):
        # Преобразуем путь в объект Path
        path = Path(field_data)

        # Проверяем, существует ли директория на уровне выше
        if not path.parent.exists():
            # Если директория не существует, создаём её
            path.parent.mkdir(parents=True, exist_ok=True)

        return str(path)


telethon_container_settings = TelethonClientContainer()
