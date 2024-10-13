import asyncio
import json
from abc import ABC, abstractmethod
from typing import List, Optional, AsyncGenerator

from faststream.nats import NatsBroker

from loguru import logger

from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.queue import NatsReplyRequestQueueMessageDTOStreem, TelegramObjectHeadersDTO
from src.schemas.service.response import ResponseModel
from src.schemas.service.user import UserDTOQueue, UserDTO, UserDTOBase
from src.services.publisher.publisher import NatsPublisher


class UserInformationCollector(ABC):

    @abstractmethod
    async def collect_users_information(self, *args, **kwargs) -> List['UserDTO']:
        pass


class TelegramUserInformationCollector(UserInformationCollector):
    PARSE_SUBJECT = "parser.gather.information.many_users"

    def __init__(self, publisher: NatsPublisher):
        self.publisher = publisher

    async def collect_users_information(self, users: List[UserDTOBase], client: TelegramClientDTOGet) -> Optional[
        List[UserDTO]]:
        message = self._create_nats_message(users, client)
        try:
            response = await self.publisher.request_reply(nats_message=message)
            if response:
                logger.info(f"Ответ от сервера получен")
                return await self._parse_users_info(response)
        except Exception as e:
            logger.error(f"Ошибка при сборе информации о пользователях: {e}")
            raise

        return None

    def _create_nats_message(self, users: List[UserDTOBase],
                             client: TelegramClientDTOGet) -> NatsReplyRequestQueueMessageDTOStreem:
        user_dicts = [user.dict() for user in users]

        headers = TelegramObjectHeadersDTO(
            tg_client=json.dumps(client.dict()),
            tg_user_users=json.dumps(user_dicts)
        )

        return NatsReplyRequestQueueMessageDTOStreem(
            subject=self.PARSE_SUBJECT,
            headers=headers,
        )

    async def _parse_users_info(self, response: str) -> Optional[List[UserDTO]]:
        users = []
        async for user in self._user_generator(response):
            user_dto = await self.convert_to_user_dto(user)
            users.append(user_dto)
        return users if users else None

    @staticmethod
    async def _user_generator(response: str) -> AsyncGenerator[UserDTOQueue, None]:
        response_model = ResponseModel.model_validate_json(response)
        for user_data in response_model.response.data:
            yield user_data

    @staticmethod
    async def convert_to_user_dto(user_data: UserDTOQueue) -> UserDTO:
        return UserDTO(**user_data.dict())

    # async def parse_users_info(self, response: str) -> List[UserDTO]:
    #     response_model = ResponseModel.model_validate_json(response)
    #     users = await asyncio.gather(*(self.convert_to_user_dto(user_data) for user_data in response_model.response.data))
    #     return list(users) if users else None


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
