import json

from aiocache import cached, Cache
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Union, List, Optional, Any, Tuple, Dict

from loguru import logger

from configs.communicator import communicator_first_message_policy
from src.schemas.communicator.distanation import NatsDestinationDTO
from src.schemas.communicator.message import IncomeUserMessageDTOQueue
from src.schemas.communicator.prompt import PromptDTO
from src.schemas.communicator.request import SingleRequestDTO, ContextRequestDTO
from src.schemas.communicator.response import SingleResponseDTO, ContextResponseDTO
from src.schemas.service.assistant import AssistantDTOGet
from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.message import AssistantMessageDTOPost, UserMessageDTOPost
from src.schemas.service.user import UserDTOFull, UserDTOBase
from src.services.communicator.prompt_generator import PromptGenerator, ExtendedPingPromptGenerator
from src.services.communicator.request import SingleRequest, ContextRequest
from src.database.postgres.models.enum_types import UserStatusEnum
from src.database.repository.storage import RepoStorage

from abc import ABC
from typing import Union

from src.schemas.service.queue import NatsQueueMessageDTOSubject, NatsQueueMessageDTOStreem, TelegramTimeDelaHeadersDTO, \
    TelegramSimpleHeadersDTO, TelegramObjectHeadersDTO
from src.services.publisher.publisher import NatsPublisher


# TODO сделать рефактор и вынести все что можно вынести в модуль
class MessageGeneratorTimeDelay:

    def __init__(self, settings: dict = None):
        self.settings = settings if settings else self._load_settings()

    @staticmethod
    def _load_settings():
        return {
            "send_policy": communicator_first_message_policy.people_in_bunch,
            "delay_between_bunch": communicator_first_message_policy.delay_between_bunch,
            "delay_between_messages": communicator_first_message_policy.delay_between_messages,
        }

    def generate(self, users: List[UserDTOBase]):
        current_time = datetime.now(tz=timezone.utc)  # Текущее время

        people_per_day = self.settings.get("send_policy", 10)
        delay_between_messages = self.settings.get("delay_between_messages", timedelta(minutes=4))
        delay_between_bunch = self.settings.get("delay_between_bunch", timedelta(hours=24))

        right_border = 0

        for i, left_border in enumerate(range(0, len(users), people_per_day)):
            if right_border + people_per_day > len(users):
                right_border = len(users)
            else:
                right_border = left_border + people_per_day
            logger.info(f"_______USER___GROUP__{i}________")
            for j, user in enumerate(users[left_border:right_border]):
                next_time_message = current_time + (j * delay_between_messages) + (i * delay_between_bunch)
                logger.info(f'User ID: {user}, Next Time Message: {next_time_message}')
                yield next_time_message, user


class MessageFromContext:
    def __init__(self, repository):
        self.repository = repository

    async def form_context(self, telegram_id: int) -> List[Dict[str, str]]:
        try:
            user_messages_future = self.repository.message_repo.user.get_user_messages_by_user_telegram_id(
                telegram_id=telegram_id)
            assistant_messages_future = self.repository.message_repo.assistant.get_all_assistent_messages_by_user_telegram_id(
                telegram_id=telegram_id)
            user_messages, assistant_messages = await asyncio.gather(user_messages_future, assistant_messages_future)

            if not user_messages and not assistant_messages:
                raise ValueError(f"No messages found for user ID: {telegram_id}")

            messages = self._combine_and_format_messages(user_messages, assistant_messages)
            sorted_messages = sorted(messages, key=lambda x: x[1])
            return [msg[0] for msg in sorted_messages]
        except Exception as e:
            logger.error(f"Error forming context for user {telegram_id}: {str(e)}")
            raise

    def _combine_and_format_messages(self, user_messages: List[Any], assistant_messages: List[Any]) -> List[
        Tuple[Dict[str, str], datetime]]:
        formatted_messages = []
        formatted_messages.extend(self._format_messages(user_messages, "user"))
        formatted_messages.extend(self._format_messages(assistant_messages, "assistant"))
        return formatted_messages

    @staticmethod
    def _format_messages(messages: List[Any], role: str) -> List[Tuple[Dict[str, str], datetime]]:
        return [({"role": role, "content": msg.text}, msg.created_at) for msg in messages]


class BaseMessageHandler(ABC):
    def __init__(self, publisher: 'NatsPublisher', repository: 'RepoStorage',
                 prompt_generator: "ExtendedPingPromptGenerator"):
        self.repository = repository
        self.publisher = publisher
        self.prompt_generator = prompt_generator

    async def publish_message(self, queue_object: Union[NatsQueueMessageDTOSubject, NatsQueueMessageDTOStreem]):
        try:
            if isinstance(queue_object, NatsQueueMessageDTOSubject):
                await self.publisher.publish_message_to_subject(subject_message=queue_object)
            elif isinstance(queue_object, NatsQueueMessageDTOStreem):
                await self.publisher.publish_message_to_stream(stream_message=queue_object)
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_user_ids(self, research_id) -> Optional[List[int]]:
        users = await self.repository.user_in_research_repo.short.get_users_by_research_id(research_id=research_id)
        return [int(user.tg_user_id) for user in users] if users else None

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_client_name(self, research_id=None, client_telegram_id=None) -> Optional[TelegramClientDTOGet]:
        if research_id is not None and client_telegram_id is None:
            return await self.repository.client_repo.get_client_by_research_id(research_id)
        elif client_telegram_id is not None and research_id is None:
            return await self.repository.client_repo.get_client_by_telegram_id(client_telegram_id)
        return None

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_assistant_by_user_telegram_id(self, telegram_id: int) -> Optional[AssistantDTOGet]:
        return await self.repository.assistant_repo.get_assistant_by_user_tgelegram_id(telegram_id=telegram_id)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_assistant(self, research_id) -> int:
        research = await self.repository.research_repo.short.get_research_by_id(research_id=research_id)
        return research.assistant_id

    async def form_single_request(self, research_id=None, assistant_id=None) -> SingleRequestDTO:

        prompt: PromptDTO = await (self.prompt_generator.generate_first_message_prompt(
            research_id=research_id) if research_id else self.prompt_generator.generate_common_prompt(assistant_id))
        return SingleRequestDTO(user_prompt=prompt.user_prompt, system_prompt=prompt.system_prompt,
                                assistant_message=prompt.assistant_message)

    async def save_assistant_message(self, content: str,
                                     user_id: int,
                                     assistant_id: int,
                                     client: 'TelegramClientDTOGet'):

        await self.repository.message_repo.assistant.save_new_message(
            values=AssistantMessageDTOPost(
                text=content,
                chat_id=user_id,
                to_user_id=user_id,
                assistant_id=assistant_id,
                telegram_client_id=client.client_id
            ).dict())

    async def save_user_message(self, content: str, user_id: int, chat_id: int = None, is_voice: bool = False,
                                is_media: bool = False):
        chat_id = chat_id if chat_id else user_id
        await self.repository.message_repo.user.save_new_message(
            values=UserMessageDTOPost(
                from_user=user_id,
                chat=chat_id,
                media=is_media,
                voice=is_voice,
                text=content
            ).dict())


class MessageFirstSend(BaseMessageHandler):
    """
    Отправляет первое сообщнеи
    для работы необходимо пользовательтское имя чтобы отправить сообщение незнакомому пользователю и его telegram id чтобы
    сохранить сообщение в базе данных
    """

    def __init__(self, publisher: 'NatsPublisher',
                 repository: 'RepoStorage',
                 single_request: 'SingleRequest',
                 prompt_generator: 'PromptGenerator'):
        super().__init__(publisher, repository, prompt_generator)
        self.message_delay_generator = MessageGeneratorTimeDelay()
        self.single_request = single_request

    async def handle(self,
                     users: List[UserDTOBase],
                     research_id: int,
                     destination_configs: 'NatsDestinationDTO'):

        client = await self.get_client_name(research_id)
        assistant_id = await self.get_assistant(research_id)

        if not users or not client:
            raise ValueError("No users found or client not available for the given research ID")

        tasks = [
            self._process_user(user, send_time, research_id, client, assistant_id, destination_configs)
            for send_time, user in self.message_delay_generator.generate(users=users)
        ]

        await asyncio.gather(*tasks)

    async def _process_user(self,
                            user: UserDTOBase,
                            send_time: datetime,
                            research_id: int,
                            client: 'TelegramClientDTOGet',
                            assistant_id: int,
                            destination_configs: 'NatsDestinationDTO'):
        try:

            single_request_object = await self.form_single_request(research_id)
            content: SingleResponseDTO = await self.single_request.get_response(single_obj=single_request_object)
            await self._publish_and_save_message(content, user, send_time, client, assistant_id, destination_configs)
            await self._change_user_status_in_progress(telegram_id=user.tg_user_id)

        except Exception as e:
            logger.error(f"Error processing user {user.tg_user_id}: {e}", exc_info=True)
            raise e

    async def _publish_and_save_message(self,
                                        content: "SingleResponseDTO",
                                        user: UserDTOBase,
                                        send_time: datetime,
                                        client: 'TelegramClientDTOGet', assistant_id: int,
                                        destination_configs: 'NatsDestinationDTO'):

        publish_message = await self._create_publish_message(content, user, send_time, client, destination_configs)
        await self.publisher.publish_message_to_stream(stream_message=publish_message)
        await self.save_assistant_message(content.response, user.tg_user_id, assistant_id, client)

    async def _create_publish_message(self,
                                      content: 'SingleResponseDTO',
                                      user: UserDTOBase,
                                      send_time: datetime,
                                      client: 'TelegramClientDTOGet',
                                      destination_configs: 'NatsDestinationDTO') -> 'NatsQueueMessageDTOStreem':

        headers = TelegramTimeDelaHeadersDTO(
            tg_client_name=str(client.name),
            user=json.dumps(user.dict()),
            send_time_msg_timestamp=str(datetime.now(tz=timezone.utc).timestamp()),
            send_time_next_message_timestamp=str(send_time.timestamp())
        )
        return self.publisher.form_stream_message(
            message=content.response,
            subject=destination_configs.subject,
            stream=destination_configs.stream,
            headers=headers.dict()
        )

    async def _change_user_status_in_progress(self, telegram_id: int) -> bool:
        try:
            user = await self.repository.user_in_research_repo.short.update_user_status(telegram_id=telegram_id,
                                                                                        status=UserStatusEnum.IN_PROGRESS)
            return True if user else False
        except Exception as e:
            raise e




class MessageAnswer(BaseMessageHandler):
    def __init__(self,
                 publisher,
                 repository,
                 prompt_generator: "ExtendedPingPromptGenerator",
                 context_request: "ContextRequest"):
        super().__init__(publisher, repository, prompt_generator)
        self.context_former = MessageFromContext(repository=repository)
        self.context_request = context_request

    async def _publish_and_save_message(self,
                                        content: "ContextResponseDTO",
                                        user: UserDTOBase,
                                        client: 'TelegramClientDTOGet',
                                        assistant_id: int,
                                        destination_configs: 'NatsDestinationDTO'):
        publish_message = await self._create_publish_message(content, user, client, destination_configs)
        await self.publisher.publish_message_to_stream(stream_message=publish_message)
        await self.save_assistant_message(content.response, user.tg_user_id, assistant_id, client)

    async def _create_publish_message(self, content: "ContextResponseDTO",
                                      user: UserDTOBase,
                                      client: 'TelegramClientDTOGet',
                                      destination_configs: 'NatsDestinationDTO') -> 'NatsQueueMessageDTOStreem':
        headers = TelegramObjectHeadersDTO(
            tg_client=str(client.name),
            user=json.dumps(user.dict())
        )
        return self.publisher.form_stream_message(
            message=content.response,
            subject=destination_configs.subject,
            stream=destination_configs.stream,
            headers=headers.dict()
        )


class ResearchMessageAnswer(MessageAnswer):
    async def handle(self,
                     message: IncomeUserMessageDTOQueue,
                     destination_configs: NatsDestinationDTO,
                     research_id: int):
        await self.save_user_message(content=message.message,
                                     user_id=message.from_user,
                                     chat_id=message.chat,
                                     is_voice=message.voice,
                                     is_media=message.media)

        assistant = await self.get_assistant(research_id=research_id)
        client: TelegramClientDTOGet = await self.get_client_name(research_id)
        context = await self.context_former.form_context(telegram_id=message.from_user)

        prompt: PromptDTO = await self.prompt_generator.research_prompt_generator.generate_prompt(
            research_id=research_id)
        response: ContextResponseDTO = await self.context_request.get_response(
            context_obj=ContextRequestDTO(system_prompt=prompt.system_prompt, user_prompt=prompt.user_prompt,
                                          context=context))
        await self._publish_and_save_message(content=response,
                                             client=client,
                                             user=UserDTOBase(username=message.username, tg_user_id=message.from_user),
                                             assistant_id=assistant,
                                             destination_configs=destination_configs)


class CommonMessageAnswer(MessageAnswer):

    # TODO кварги костыль нужно убрать метод должен работать для вскех вынести в инком мессадж или дополнительнчый класс
    async def handle(self,
                     message: IncomeUserMessageDTOQueue,
                     destination_configs: NatsDestinationDTO,
                     **kwargs):
        await self.save_user_message(content=message.message,
                                     user_id=message.from_user,
                                     chat_id=message.chat,
                                     is_voice=message.voice,
                                     is_media=message.media)

        assistant: AssistantDTOGet = await self.get_assistant_for_free_talk()
        client: TelegramClientDTOGet = await self.get_client_name(client_telegram_id=message.client_telegram_id)
        context = await self.context_former.form_context(telegram_id=message.from_user)

        prompt: PromptDTO = await self.prompt_generator.generate_common_prompt(
            assistant_id=assistant.assistant_id)
        response: ContextResponseDTO = await self.context_request.get_response(
            context_obj=ContextRequestDTO(system_prompt=prompt.system_prompt, user_prompt=prompt.user_prompt,
                                          context=context))

        await self._publish_and_save_message(content=response,
                                             client=client,
                                             user=UserDTOBase(username=message.username,
                                                              tg_user_id=message.from_user),
                                             assistant_id=assistant.assistant_id,
                                             destination_configs=destination_configs)

    # TODO вынести выдачу ассситентов в отлдельный класс заебал
    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_assistant_for_free_talk(self) -> Optional[AssistantDTOGet]:
        assistants = await self.repository.assistant_repo.get_all_assistants()
        if not assistants:
            logger.error("No assistants in database")
            raise ValueError("No assistants")
        return next((asis for asis in assistants if asis.for_conversation), None)


# TODO разные классы заддач разщнести по разным классам и вынести метод паблишишера эти классыы только фомрирует ответ от ИИ
# Ответы от ИИ какие бывают ...
class PingMessage(MessageAnswer):
    """ сообщения для пинга пользователоей в иследовании """

    async def handle(self, user: UserDTOBase, message_number, research_id: int,
                     destination_configs: NatsDestinationDTO):
        assistant_id: int = await self.get_assistant(research_id=research_id)
        client: TelegramClientDTOGet = await self.get_client_name(research_id)
        context = await self.context_former.form_context(telegram_id=user.tg_user_id)
        prompt: PromptDTO = await self.prompt_generator.ping_prompt_generator.generate_prompt(
            message_number=message_number)

        response: ContextResponseDTO = await self.context_request.get_response(
            context_obj=ContextRequestDTO(system_prompt=prompt.system_prompt, user_prompt=prompt.user_prompt,
                                          context=context))

        # TODO убрать этот метод в коммуникатор я думаю это ответсвенность коммуникатора за публикацию
        await self._publish_and_save_message(content=response,
                                             client=client,
                                             user=user,
                                             assistant_id=assistant_id,
                                             destination_configs=destination_configs
                                             )
