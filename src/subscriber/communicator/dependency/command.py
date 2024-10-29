import json
from typing import List, Dict

from faststream import Context
from faststream.nats import NatsMessage
from loguru import logger

from src.subscriber.communicator.schemas.command import UserDTOBase, CommandStartDiologDTO, CommandPingUserDTO


def form_user_info(users: str) -> List[UserDTOBase]:
    try:
        deserialization_users: List[Dict] = json.loads(users)
    except Exception as e:
        raise e
    else:
        users_dto = [UserDTOBase(name=user["name"], tg_user_id=user["tg_user_id"])
                     for user in deserialization_users]
        return users_dto


async def get_command_start_dialog_data_from_headers(body: str, msg: NatsMessage,
                                                     context=Context()) -> CommandStartDiologDTO:
    # Проверка наличия заголовков
    headers = msg.headers
    if not headers:
        logger.error("Headers are missing from the message.")
        raise ValueError("Headers are missing from the message.")

    # Извлечение и преобразование значений из заголовков
    try:
        users = headers.get("users", 0)
        research_id = int(headers.get("research_id", -1))
        # Проверка критических значений
        if users == 0:
            logger.error("Missing user id in headers.")
            raise ValueError("Missing user id in headers.")

        if research_id == -1:
            logger.error("Missing client research id in headers.")
            raise ValueError("Missing client research id in headers.")



    except Exception as e:
        print(e)

    else:
        users_dto: List[UserDTOBase] = form_user_info(users)
        return CommandStartDiologDTO(
            research_id=research_id,
            users=users_dto
        )


async def get_command_ping_user(body:str, msg: NatsMessage) -> CommandPingUserDTO:
    # Проверка наличия заголовков

    decode_message = json.loads(msg.body.decode("utf-8"))
    print("__________DECODE BODY", decode_message)
    if not decode_message:
        logger.error("Body are missing from the message.")
        raise ValueError("Body are missing from the message.")

    # Извлечение и преобразование значений из заголовков
    try:
        user:dict = decode_message.get("user", 0)
        research_id = int(decode_message.get("research_id", -1))
        message_number = int(decode_message.get("message_number", -1))

        # Проверка критических значений
        if user == 0:
            logger.error("Missing user id in headers.")
            raise ValueError("Missing user id in headers.")

        if research_id == -1:
            logger.error("Missing research id in headers.")
            raise ValueError("Missing research id in headers.")

        if message_number == -1:
            logger.error("Missing prompt_number in headers.")
            raise ValueError("Missing prompt_number in headers.")

    except Exception as e:
        print(e)

    else:
        users_dto: UserDTOBase = UserDTOBase(**user)
        return CommandPingUserDTO(
            research_id=research_id,
            user=users_dto,
            message_number=message_number,
        )
