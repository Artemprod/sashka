from aiocache import cached, Cache
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Union, List, Optional, Any, Tuple, Dict

from loguru import logger

from src.schemas.communicator.distanation import NatsDestinationDTO
from src.schemas.communicator.message import IncomeUserMessageDTOQueue
from src.schemas.communicator.prompt import PromptDTO
from src.schemas.communicator.request import SingleRequestDTO, ContextRequestDTO
from src.schemas.communicator.response import SingleResponseDTO, ContextResponseDTO
from src.schemas.service.assistant import AssistantDTOGet
from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.message import AssistantMessageDTOPost, UserMessageDTOPost
from src.schemas.service.user import UserDTOFull
from src.services.communicator.prompt_generator import PromptGenerator
from src.services.communicator.request import SingleRequest, ContextRequest
from src_v0.database.postgres.models.enum_types import UserStatusEnum
from src_v0.database.repository.storage import RepoStorage

from abc import ABC
from typing import Union

from src.schemas.service.queue import NatsQueueMessageDTOSubject, NatsQueueMessageDTOStreem, TelegramTimeDelaHeadersDTO, \
    TelegramSimpleHeadersDTO
from src.services.publisher.messager import NatsPublisher



class BaseMessageHandler(ABC):
    def __init__(self, publisher: 'NatsPublisher', repository: 'RepoStorage', prompt_generator: 'PromptGenerator'):
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
    async def get_client_name(self, research_id) -> Optional[TelegramClientDTOGet]:
        return await self.repository.client_repo.get_client_by_research_id(research_id)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_assistant_by_user_telegram_id(self, telegram_id: int) -> Optional[AssistantDTOGet]:
        return await self.repository.assistant_repo.get_assistant_by_user_tgelegram_id(telegram_id=telegram_id)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_assistant(self, research_id) -> int:
        research = await self.repository.research_repo.short.get_research_by_id(research_id=research_id)
        return research.assistant_id

    async def form_single_request(self, research_id=None) -> SingleRequestDTO:
        prompt = await (self.prompt_generator.generate_first_message_prompt(
            research_id=research_id) if research_id else self.prompt_generator.generate_common_prompt())
        return SingleRequestDTO(user_prompt=prompt.user_prompt, system_prompt=prompt.system_prompt)

    async def save_assistant_message(self, content: str, user_id: int, assistant_id: int,
                                     client: 'TelegramClientDTOGet'):
        await self.repository.message_repo.assistant.save_new_message(
            values=AssistantMessageDTOPost(
                text=content, chat_id=user_id,
                to_user_id=user_id, assistant_id=assistant_id,
                telegram_client_id=client.telegram_client_id
            ))

    async def save_user_message(self, content: str, user_id: int, chat_id: int = None, is_voice: bool = False,
                                is_media: bool = False):
        chat_id = chat_id if chat_id else user_id
        await self.repository.message_repo.user.save_new_message(
            values=UserMessageDTOPost(
                from_user=user_id, chat=chat_id,
                media=is_media, voice=is_voice,
                text=content
            ))


class MessageFirstSend(BaseMessageHandler):
    def __init__(self, publisher: 'NatsPublisher', repository: 'RepoStorage', single_request: 'SingleRequest',
                 message_generator: 'MessageGeneratorTimeDelay', prompt_generator: 'PromptGenerator'):
        super().__init__(publisher, repository, prompt_generator)
        self.message_delay_generator = message_generator
        self.single_request = single_request

    async def handle(self, research_id: int, destination_configs: 'NatsDestinationDTO'):
        user_ids = await self.get_user_ids(research_id)
        client = await self.get_client_name(research_id)
        assistant_id = await self.get_assistant(research_id)

        if not user_ids or not client:
            raise ValueError("No users found or client not available for the given research ID")

        tasks = [
            self._process_user(user_id, send_time, research_id, client, assistant_id, destination_configs)
            for send_time, user_id in self.message_delay_generator.generate(user_ids=user_ids)
        ]

        await asyncio.gather(*tasks)

    async def _process_user(self, user_id: int, send_time: datetime, research_id: int, client: 'TelegramClientDTOGet',
                            assistant_id: int, destination_configs: 'NatsDestinationDTO'):
        try:
            single_request_object = await self.form_single_request(research_id)
            content: SingleResponseDTO = await self.single_request.get_response(single_obj=single_request_object)
            await self._publish_and_save_message(content, user_id, send_time, client, assistant_id, destination_configs)
            await self._change_user_status_in_progress(user_id)
        except Exception as e:
            logger.error(f"Error processing user {user_id}: {e}", exc_info=True)

    async def _publish_and_save_message(self, content: "SingleResponseDTO", user_id: int, send_time: datetime,
                                        client: 'TelegramClientDTOGet', assistant_id: int,
                                        destination_configs: 'NatsDestinationDTO'):
        publish_message = await self._create_publish_message(content, user_id, send_time, client, destination_configs)
        await self.publisher.publish_message_to_stream(stream_message=publish_message)
        await self.save_assistant_message(content.response, user_id, assistant_id, client)

    async def _create_publish_message(self, content: 'SingleResponseDTO', user_id: int, send_time: datetime,
                                      client: 'TelegramClientDTOGet',
                                      destination_configs: 'NatsDestinationDTO') -> 'NatsQueueMessageDTOStreem':
        headers = TelegramTimeDelaHeadersDTO(
            tg_client_name=str(client.name),
            tg_user_userid=str(user_id),
            send_time_msg_timestamp=str(datetime.now(tz=timezone.utc).timestamp()),
            send_time_next_message_timestamp=str(send_time.timestamp())
        )
        return await self.publisher.form_stream_message(
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
            raise


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


class MessageAnswer(BaseMessageHandler):
    def __init__(self, context_former: MessageFromContext, publisher, repository, prompt_generator,
                 context_request: "ContextRequest"):
        super().__init__(publisher, repository, prompt_generator)
        self.context_former = context_former
        self.context_request = context_request

    async def _publish_and_save_message(self, content: "ContextResponseDTO", user_id: int,
                                        client: 'TelegramClientDTOGet', assistant_id: int,
                                        destination_configs: 'NatsDestinationDTO'):
        publish_message = await self._create_publish_message(content, user_id, client, destination_configs)
        await self.publisher.publish_message_to_stream(stream_message=publish_message)
        await self.save_assistant_message(content.response, user_id, assistant_id, client)

    async def _create_publish_message(self, content: "ContextResponseDTO", user_id: int, client: 'TelegramClientDTOGet',
                                      destination_configs: 'NatsDestinationDTO') -> 'NatsQueueMessageDTOStreem':
        headers = TelegramSimpleHeadersDTO(
            tg_client_name=str(client.name),
            tg_user_userid=str(user_id)
        )
        return await self.publisher.form_stream_message(
            message=content.response,
            subject=destination_configs.subject,
            stream=destination_configs.stream,
            headers=headers.dict()
        )


class ResearchMessageAnswer(MessageAnswer):
    async def handle(self, message: IncomeUserMessageDTOQueue, destination_configs: NatsDestinationDTO,
                     research_id: int):
        await self.save_user_message(content=message.text, user_id=message.from_user, chat_id=message.chat,
                                     is_voice=message.voice, is_media=message.media)
        assistant = await self.get_assistant(research_id=research_id)
        client: TelegramClientDTOGet = await self.get_client_name(research_id)
        context = await self.context_former.form_context(telegram_id=message.from_user)
        prompt = await self.prompt_generator.research_prompt_generator.generate_prompt(research_id=research_id)
        response: ContextResponseDTO = await self.context_request.get_response(
            context_obj=ContextRequestDTO(prompt=prompt, context=context))
        await self._publish_and_save_message(content=response, client=client, user_id=message.from_user,
                                             assistant_id=assistant, destination_configs=destination_configs)


class CommonMessageAnswer(MessageAnswer):
    async def handle(self, message: IncomeUserMessageDTOQueue, destination_configs: NatsDestinationDTO):
        await self.save_user_message(content=message.text, user_id=message.from_user, chat_id=message.chat,
                                     is_voice=message.voice, is_media=message.media)
        assistant: AssistantDTOGet = await self.get_assistant_for_free_talk()
        client: TelegramClientDTOGet = await self.get_client_name(research_id=message.client_telegram_id)
        context = await self.context_former.form_context(telegram_id=message.from_user)
        prompt = await self.prompt_generator.research_prompt_generator.generate_common_prompt(
            assistant_id=assistant.assistant_id)
        response: ContextResponseDTO = await self.context_request.get_response(
            context_obj=ContextRequestDTO(prompt=prompt, context=context))
        await self._publish_and_save_message(content=response, client=client, user_id=message.from_user,
                                             assistant_id=assistant.assistant_id,
                                             destination_configs=destination_configs)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_assistant_for_free_talk(self) -> Optional[AssistantDTOGet]:
        assistants = await self.repository.assistant_repo.get_all_assistants()
        return next((asis for asis in assistants if asis.for_conversation), None)
