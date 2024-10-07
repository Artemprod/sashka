import ast
import asyncio
import json
from datetime import datetime
from typing import Annotated, Optional, List, Union

from faststream import Context, Depends
from faststream.nats import NatsRouter, NatsBroker, NatsMessage
from loguru import logger
from pydantic import BaseModel, Field
from pyrogram import Client
from pyrogram.types import User

from src_v0.database.repository.storage import RepoStorage
from src_v0.resrcher.user_cimmunication import Communicator
from src_v0.telegram_client.client.container import ClientsManager

parser_router = NatsRouter()
broker = NatsBroker()


# @router.subscriber(subject="parser.gather.information.many_users")
# async def send_message(body: str, msg:NatsMessage , context=Context()):
#     """отправляет сообщение """
#     container: ClientsManager = context.get("container")
#     users = ast.literal_eval(msg.headers.get("Tg-Users-UsersId'"))
#     client: Client = container.get_client_by_name(name="test_e85d412a-bb82-4271-8197-1b3a284ed647")
#     await client.get_users(user_ids=users)
#
#
#     # msg_data = await client.send_message(user.id, text=body)
#
#     await msg.ack()
class SuccessResponse(BaseModel):
    status: str = "success"
    data: List["UserInfo"]

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    status: str = "error"
    error_message: str

    class Config:
        from_attributes = True


class ResponseModel(BaseModel):
    response: Union["SuccessResponse", "ErrorResponse"]

    class Config:
        from_attributes = True


class Datas(BaseModel):
    users: List[int] = Field(default_factory=list)
    client_name: str
    client: 'Client'
    container: 'ClientsManager'

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True


class UserInfo(BaseModel):
    tg_user_id: int
    is_contact: bool
    is_mutual_contact: bool
    is_deleted: bool
    is_bot: bool
    is_verified: bool
    is_restricted: bool
    is_scam: bool
    is_fake: bool
    is_support: bool
    is_premium: bool
    name: Optional[str] = None
    last_name: Optional[str] = None
    status: str
    last_online_date: Optional[datetime]  # Можно оставить datetime, а не строку
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True
        # Преобразование даты в строку при сериализации
        json_encoders = {
            datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")
        }


async def derive_data(msg: NatsMessage, context=Context()) -> Datas:
    users = ast.literal_eval(msg.headers.get("Tg-Users-UsersId"))
    client_name = msg.headers.get("Tg-Client-Name")
    container: 'ClientsManager' = context.get("container")
    client: 'Client' = container.get_client_by_name(name=client_name)
    print(msg)

    return Datas(
        users=users,
        client_name=client_name,
        client=client,
        container=container
    )



async def form_user_information(user: 'User') -> UserInfo:
    return UserInfo(
        tg_user_id=user.id,
        is_contact=user.is_contact,
        is_mutual_contact=user.is_mutual_contact,
        is_deleted=user.is_deleted,
        is_bot=user.is_bot,
        is_verified=user.is_verified,
        is_restricted=user.is_restricted,
        is_scam=user.is_scam,
        is_fake=user.is_fake,
        is_support=user.is_support,
        is_premium=user.is_premium,
        name=user.first_name,
        last_name=user.last_name,
        status=user.status.value,
        last_online_date=user.last_online_date,
        phone_number=user.phone_number
    )


async def gather_information(user_data: List['User']):
    return await asyncio.gather(*(form_user_information(user) for user in user_data))


@parser_router.subscriber(subject="parser.gather.information.many_users")
async def send_message(msg: 'NatsMessage', data: Datas = Depends(derive_data)):
    logger.info("Подключаюсь к брокеру...")

    await broker.connect()
    logger.info("Подключение установлено")
    try:
        user_data = await data.client.get_users(user_ids=["test_ai"])
        print()
        user_info = await gather_information(user_data)
        response_data: ResponseModel = ResponseModel(response=SuccessResponse(data=user_info))

    except Exception as e:
        logger.error("An error occurred:", e)
        response_data: ResponseModel = ResponseModel(response=ErrorResponse(error_message=str(e)))

    if msg.reply_to:
        logger.info(f"Вот такая дата {response_data.model_dump_json()}", )
        queue_data = response_data.model_dump_json(indent=3, serialize_as_any=True)
        await broker.publish(message=queue_data, subject=msg.reply_to, reply_to=msg.reply_to)
        await broker.close()


