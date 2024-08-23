import asyncio
import datetime

import pyrogram
from faststream import Context
from faststream.nats import NatsRouter
from loguru import logger

from src.database.connections.redis_connect import RedisClient
from src.database.repository.storage import RepoStorage
from src.telegram_client.client.model import ClientConfigDTO
from src.telegram_client.exceptions.autrization import AutorizationFaildError

database_router = NatsRouter()


async def wait_session(repository,redis_connection_manager,configs):
    session_string = None
    is_authorized = False

    while not is_authorized:
        client_info = await redis_connection_manager.get_client_connection_info(connection_name="CONNECTIONS",
                                                                                client_name=configs.name)
        is_authorized = client_info["is_authorized"]
        session_string = client_info["session"]
        await asyncio.sleep(10)
        if is_authorized and session_string:
            print(session_string)
            parse_mode = configs.parse_mode
            if isinstance(parse_mode, pyrogram.enums.ParseMode):
                parse_mode = parse_mode.value
            try:
                new_client = await repository.client_repo.save(
                    name=configs.name,
                    api_id=configs.api_id,
                    api_hash=configs.api_hash,
                    app_version=configs.app_version,
                    device_model=configs.device_model,
                    system_version=configs.system_version,
                    lang_code=configs.lang_code,
                    test_mode=configs.test_mode,
                    session_string=session_string,
                    phone_number=configs.phone_number,
                    password=configs.password,
                    parse_mode=parse_mode,
                    workdir=configs.workdir,
                    created_at=datetime.datetime.now()
                )

                logger.info(f"New client saved: {configs.name}")
                return new_client
            except Exception as e:
                logger.error(f"Error saving new client: {e}")
                return None
            # except AutorizationFaildError:
            #     logger.info(f"Stop saving: {configs.name}")


@database_router.subscriber("save_client")
async def save_new_client(message, context=Context()):
    """Сохраняет нового клиента в базе данных"""
    # Как получить сесисию
    # Варинт 1:
    # 1. Иметь доступ до редис информаци
    # 2. Запрос к редис по имени клиента : Аторизован ?
    # 3. Если да то забрать сесиию если нет ждать 10 споаторить ( настройики обновления редлис глобаольные )
 #TODO Нужно сделать отказ от цикла когда ошикба авторизации или же сделать отправку сообщения только после успешного логина
    print(message)
    repository: RepoStorage = context.get("repository")
    redis_connection_manager:RedisClient = context.get("redis_connection_manager")
    configs = ClientConfigDTO(**message)
    await asyncio.sleep(10)
    asyncio.create_task(wait_session(repository,redis_connection_manager,configs))

