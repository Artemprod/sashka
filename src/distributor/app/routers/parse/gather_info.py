import ast
import asyncio
from datetime import datetime
from typing import Optional, List, Union

from faststream import Context, Depends
from faststream.nats import NatsRouter, NatsBroker, NatsMessage
from loguru import logger
from pydantic import BaseModel, Field
from pyrogram.errors import PeerIdInvalid

router = NatsRouter()
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


class UserDTOBase(BaseModel):
    name: Optional[str]
    tg_user_id: Optional[int]


class Datas(BaseModel):
    users: List[UserDTOBase] = Field(default_factory=list)
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


class TelegramClientDTO(BaseModel):
    client_id: int
    telegram_client_id: int
    name: str
    api_id: str
    api_hash: str
    app_version: str
    device_model: str
    system_version: str

    lang_code: Optional[str] = None
    test_mode: bool = False
    session_string: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    parse_mode: Optional[str] = 'html'
    workdir: Optional[str] = None
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True


async def derive_data(msg: NatsMessage, context=Context()) -> Datas:
    print(msg.headers)
    users: list[dict] = ast.literal_eval(msg.headers.get("user"))
    users_dto = [UserDTOBase(name=user['name'], tg_user_id=user["tg_user_id"]) for user in users]
    client_dto = TelegramClientDTO.model_validate_json(msg.headers.get("tg_client"))
    container: 'ClientsManager' = context.get("container")
    client: 'Client' = container.get_client_by_name(name=client_dto.name)
    print(msg)

    return Datas(
        users=users_dto,
        client_name=client_dto.name,
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


async def gather_information(user_data: Union["types.User", List["types.User"]]):

    try:
        if isinstance(user_data, list):
            return await asyncio.gather(*(form_user_information(user) for user in user_data))
        else:
            return await form_user_information(user_data)
    except Exception as e:
        logger.error(e)
        raise e


async def make_request(data: Datas) -> Union["types.User", List["types.User"]]:
    try:
        user_ids: List[int] = [user.tg_user_id for user in data.users]
        return await data.client.get_users(user_ids=user_ids)

    except PeerIdInvalid:
        logger.warning("PeerIdInvalid: Trying to send by ID.")
        user_names: List[str] = [user.name for user in data.users]
        return await data.client.get_users(user_ids=user_names)


@router.subscriber(subject="parser.gather.information.many_users")
async def parse_user_information(msg: 'NatsMessage', data: Datas = Depends(derive_data)):
    logger.info("Подключаюсь к брокеру...")

    await broker.connect()
    logger.info("Подключение установлено")
    try:
        user_data = await make_request(data=data)
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
