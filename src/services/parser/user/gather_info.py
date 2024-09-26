import asyncio
import random
from abc import ABC, abstractmethod
from typing import List, Any, Optional

from faststream.nats import NatsBroker, NatsMessage

import nats
from loguru import logger

from src.schemas.response import ResponseModel, SuccessResponse, ErrorResponse
from src.schemas.user import UserDTOFull, UserDTOQueue, UserDTO


class UserInformationCollector(ABC):

    @abstractmethod
    async def collect_users_information(self, *args, **kwargs) -> List['UserDTO']:
        pass


class TelegramUserInformationCollector(UserInformationCollector):
    RPC_TIMEOUT = 10.0
    MAX_RETRIES = 10

    def __init__(self, broker_url: str = "nats://localhost:4222"):
        self.broker = NatsBroker(broker_url)

    async def __aenter__(self):
        await self.broker.connect()
        logger.info("Подключение к брокеру установлено")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.broker.close()
        logger.info("Соединение с брокером закрыто")

    async def collect_users_information(self, user_telegram_ids: List[int], client_name: str) -> Optional[List[UserDTO]]:
        for attempt in range(TelegramUserInformationCollector.MAX_RETRIES):
            try:
                users = await self._attempt_collect_info(user_telegram_ids, client_name, attempt)
                if users:
                    return users
                else:
                    continue

            except asyncio.TimeoutError:
                logger.error(f"Время ожидания ответа истекло: Попытка {attempt + 1}")
            except Exception as e:
                logger.error(f"Произошла ошибка: {e}. Попытка {attempt + 1}")


        logger.error(f"Не удалось получить ответ после {TelegramUserInformationCollector.MAX_RETRIES} попыток.")
        return None

    async def _attempt_collect_info(self, user_telegram_ids: List[int], client_name: str, attempt: int) -> Optional[List[UserDTO]]:
        logger.info(f"Отправляю запрос: Попытка {attempt + 1}")
        response = await self.broker.publish(
            headers={
                "Tg-Users-UsersId": str(user_telegram_ids),
                "Tg-Client-Name": str(client_name)
            },
            subject="parser.gather.information.many_users",
            message='Hi',
            rpc=True,
            rpc_timeout=TelegramUserInformationCollector.RPC_TIMEOUT
        )
        if response:
            logger.info(f"Ответ от сервера: {response}")
            return await self.parse_users_info(response)
        logger.warning(f"Не удалось получить ответ: Попытка {attempt + 1}")
        return

    async def parse_users_info(self, response: str) -> List[UserDTO]:
        response_model = ResponseModel.model_validate_json(response)
        users = await asyncio.gather(*(self.convert_to_user_dto(user_data) for user_data in response_model.response.data))
        return list(users) if users else None


    @staticmethod
    async def convert_to_user_dto(user_data: UserDTOQueue) -> UserDTO:
        return UserDTO(**user_data.dict())


# class APIUserInformationCollector(UserInformationCollector):
# async def collect_users_information(self, user_ids: List[int]) -> List['UserDTO']:
#     # Пример логики для сбора через API
#     return [UserDTO(user_id=user_id, user_name=f"user_{user_id}") for user_id in user_ids]

if __name__ == '__main__':
    async def main():
        async with TelegramUserInformationCollector() as a:
            info = await a.collect_users_information(user_telegram_ids=[2200096081],
                                                     client_name="test_008816cb-bb59-4a97-be15-342007189298")
            print(info)


    asyncio.run(main())
