from pydantic import BaseModel


class HeaderUserMessageDTOQueue(BaseModel):

    from_user: str
    user_name: str
    chat: str
    media: str
    voice: str
    client_telegram_id: str
