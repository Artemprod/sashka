import asyncio
import json

from faststream import Context
from faststream.nats import NatsBroker
from faststream.nats import NatsMessage
from faststream.nats import NatsRouter
from loguru import logger
from telethon import TelegramClient
from telethon.errors import UsernameNotOccupiedError, UsernameInvalidError
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import User

from src.distributor.app.schemas.parse import Datas
from src.distributor.app.schemas.parse import TelegramClientDTO
from src.distributor.app.schemas.parse import UserDTOBase
from src.distributor.app.schemas.parse import UserInfo
from src.distributor.exceptions.parse import NoUserWithNameError
from src.distributor.telegram_client.telethoncl.manager.container import TelethonClientsContainer

router = NatsRouter()
broker = NatsBroker()
async def derive_data(msg: NatsMessage, context=Context()) -> Datas:
    users: list[dict] = json.loads(msg.headers.get("user"))
    users_dto = [UserDTOBase(username=user['username'], tg_user_id=user["tg_user_id"]) for user in users]
    client_dto = TelegramClientDTO.model_validate_json(msg.headers.get("tg_client"))
    container: 'TelethonClientsContainer' = context.get("telethon_container")
    client: 'TelegramClient' = container.get_telethon_client_by_name(name=client_dto.name)
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
        phone_number=user.phone,
        language_code=user.lang_code
    )


async def gather_information(user_data):
    try:
        if isinstance(user_data, list):
            return await asyncio.gather(*(form_user_information(user) for user in user_data))
        else:
            return await form_user_information(user_data)

    except Exception as e:
        logger.error(f"Ошибка при сборе информации {e}")
        raise e


async def make_request(data: Datas):
    user_names = [user.username for user in data.users]
    user_ids = [user.tg_user_id for user in data.users]
    user_data = []
    users = user_names if user_names else user_ids
    print()
    if users:
        for user in users:
            try:
                user_info = await data.client.get_entity(user)
                user_data.append(user_info)

            except ValueError as e:
                logger.warning(f"ValueError: {e}")
                continue

            except UsernameInvalidError as e:
                logger.warning(f"UsernameInvalidError: {e}")

            except Exception as e:
                raise e

        return user_data
    else:
        logger.warning("No users")

