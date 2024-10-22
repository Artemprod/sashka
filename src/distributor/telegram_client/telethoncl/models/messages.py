import json

from pydantic import BaseModel


class OutcomeMessageDTOQueue(BaseModel):

    message: str
    from_user: str
    user_name: str
    chat: str
    media: str
    voice: str
    client_telegram_id: str

    def json_string(self) -> str:
        # Получаем данные в виде словаря
        dict_representation = self.dict()
        # Преобразуем словарь в JSON строку с кодировкой UTF-8
        json_string = json.dumps(dict_representation, ensure_ascii=False, indent=3)
        # Возвращаем строку, которая уже закодирована как UTF-8
        return json_string
