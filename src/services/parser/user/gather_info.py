import asyncio
import json
from abc import ABC, abstractmethod
from typing import List, Optional, AsyncGenerator

from faststream.nats import NatsBroker

from loguru import logger

from configs.nats_queues import nats_distributor_settings
from src.distributor.app.schemas.response import ErrorResponse
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
    PARSE_SUBJECT = nats_distributor_settings.parser.base_info.subject

    def __init__(self, publisher: NatsPublisher):
        self.publisher = publisher

    async def collect_users_information(self, users: List[UserDTOBase], client: TelegramClientDTOGet) -> Optional[
        List[UserDTO]]:
        message = self._create_nats_message(users, client)
        print("NATS MESSAGE", message)
        try:
            response = await self.publisher.request_reply(nats_message=message)
            print()
            if response:
                logger.info(f"Ответ от сервера получен")
                response_model = ResponseModel.model_validate_json(response)
                if not isinstance(response_model, ErrorResponse):
                    return await self._parse_users_info(response_model)
                else:
                    logger.warning(f"Error in response {response_model.error_message}")
        except Exception as e:
            logger.error(f"Ошибка при сборе информации о пользователях: {e}")
            raise

        return None

    def _create_nats_message(self, users: List[UserDTOBase],
                             client: TelegramClientDTOGet) -> NatsReplyRequestQueueMessageDTOStreem:
        user_dicts = [user.dict() for user in users]

        headers = TelegramObjectHeadersDTO(
            tg_client=client.json(),
            user=json.dumps(user_dicts)
        )

        return NatsReplyRequestQueueMessageDTOStreem(
            subject=self.PARSE_SUBJECT,
            headers=headers.dict(),
        )

    async def _parse_users_info(self, response: ResponseModel) -> Optional[List[UserDTO]]:
        users = []
        async for user in self._user_generator(response):
            user_dto = await self.convert_to_user_dto(user)
            users.append(user_dto)
        return users if users else None

    @staticmethod
    async def _user_generator(response: ResponseModel) -> AsyncGenerator[UserDTOQueue, None]:

        for user_data in response.response.data:
            yield user_data

    @staticmethod
    async def convert_to_user_dto(user_data: UserDTOQueue) -> UserDTO:
        return UserDTO(**user_data.dict())
