import ast
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Union

from faststream import Context, Depends
from faststream.nats import NatsRouter, NatsBroker, NatsMessage
from loguru import logger
from pydantic import BaseModel, Field
from pyrogram.errors import PeerIdInvalid
from telethon import TelegramClient
from telethon.tl.types import InputPeerUser, User, UserStatusRecently

from src.distributor.app.schemas.parse import Datas, UserDTOBase, TelegramClientDTO, UserInfo
from src.distributor.app.schemas.response import ResponseModel, SuccessResponse, ErrorResponse
from src.distributor.telegram_client.telethoncl.manager.container import TelethonClientsContainer
from src.distributor.telegram_client.telethoncl.manager.manager import TelethonManager

router = NatsRouter()
broker = NatsBroker()


async def derive_data(msg: NatsMessage, context=Context()) -> Datas:
    print(msg.headers)
    users: list[dict] = json.loads(msg.headers.get("user"))
    users_dto = [UserDTOBase(username=user['username'], tg_user_id=user["tg_user_id"]) for user in users]

    client_dto = TelegramClientDTO.model_validate_json(msg.headers.get("tg_client"))
    container: 'TelethonClientsContainer' = context.get("telethon_container")
    client: 'TelegramClient' = container.get_telethon_client_by_name(name=client_dto.name)
    print(client)
    print(msg)
    return Datas(
        users=users_dto,
        client_name=client_dto.name,
        client=client,
        container=container
    )


async def form_user_information(user: User) -> UserInfo:

    return UserInfo(
        tg_user_id=user.id,
        username=user.username,
        is_contact=user.contact,
        is_mutual_contact=user.mutual_contact,
        is_deleted=user.deleted,
        is_bot=user.bot,
        is_verified=user.verified,
        is_restricted=user.restricted,
        is_scam=user.scam,
        is_fake=user.fake,
        is_support=user.support,
        is_premium=user.premium,
        name=user.first_name,
        last_name=user.last_name,
        second_name=user.last_name,
        status=str(user.status),
        phone_number=user.phone
    )


async def gather_information(user_data):
    try:
        if isinstance(user_data, list):
            return await asyncio.gather(*(form_user_information(user) for user in user_data))
        else:
            return await form_user_information(user_data)
    except Exception as e:
        logger.error(e)
        raise e


async def make_request(data: Datas):
    user_names = [user.username for user in data.users]
    user_ids = [user.tg_user_id for user in data.users]
    try:
        print()
        # Определяем, используем ли имена или идентификаторы
        if user_names:
            return [await data.client.get_entity(name) for name in user_names]
        else:
            return [await data.client.get_entity(user_id) for user_id in user_ids]

    except ValueError as e:
        logger.warning(f"ValueError: Trying to send by name. {e}")
        print()
        # Предполагается новое самостоятельное поведение при ошибке
        return [await data.client.get_entity(name) for name in user_names]

    except Exception as e:
        print()
        logger.error(f"Error in making request: {e}")
        raise


@router.subscriber(subject="parser.gather.information.many_users", )
async def parse_user_information(msg: 'NatsMessage', data: Datas = Depends(derive_data)):
    logger.info("Подключаюсь к брокеру...")
    await broker.connect()
    logger.info("Подключение установлено")
    try:
        user_data = await make_request(data=data)
        user_info = await gather_information(user_data)
        print()
        response_data: ResponseModel = ResponseModel(response=SuccessResponse(data=user_info))

    except Exception as e:
        logger.error("An error occurred:", e)
        response_data: ResponseModel = ResponseModel(response=ErrorResponse(error_message=str(e)))

    if msg.reply_to:
        logger.info(f"Вот такая дата {response_data.model_dump_json()}", )

        queue_data = response_data.model_dump_json(indent=3, serialize_as_any=True)
        await broker.publish(message=queue_data, subject=msg.reply_to, reply_to=msg.reply_to)
        await broker.close()
