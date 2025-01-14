import json
from typing import Optional

from pydantic import BaseModel


class OutcomeMessageDTOQueue(BaseModel):

    message: str
    from_user: str
    first_name:str
    username: str
    chat: str
    media: str
    voice: str
    client_telegram_id: str
    s3_object_key: Optional[str]= None

    def json_string(self) -> str:
        # Получаем данные в виде словаря
        dict_representation = self.dict()
        # Преобразуем словарь в JSON строку с кодировкой UTF-8
        json_string = json.dumps(dict_representation, ensure_ascii=False, indent=3)
        # Возвращаем строку, которая уже закодирована как UTF-8
        return json_string
