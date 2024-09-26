import asyncio
import asyncio
import datetime

from sqlalchemy import select, func, cast, Integer, and_
from sqlalchemy.orm import aliased, selectinload, joinedload

from datasourse_for_test.resercch_imirtation import research_im_1
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.postgres.models.assistants import Assistant
from src_v0.database.postgres.models.base import ModelBase
from src_v0.database.postgres.models.client import TelegramClient
from src_v0.database.postgres.models.enum_types import ResearchStatusEnum, UserStatusEnum
from src_v0.database.postgres.models.many_to_many import UserResearch
from src_v0.database.postgres.models.message import AssistantMessage, UserMessage
from src_v0.database.postgres.models.research import Research
from src_v0.database.postgres.models.status import ResearchStatus, UserStatus

from src_v0.database.postgres.models.storage import S3VoiceStorage
from src_v0.database.postgres.models.user import User
from src_v0.database.postgres.t_data_objects import users_list, clients, user_message, voice_message, assistant_message, \
    user_research, user_statuses, research_statuses, assistant_list, reserches_list, research_owner, service
from src_v0.database.repository.data_cash import ResearchDataCashRepository
from src_v0.database.repository.owner import ResearchOwnerRepositoryFullModel
from src_v0.database.repository.research import ResearchRepositoryFullModel
from src_v0.database.repository.storage import RepoStorage
from src_v0.database.repository.user import UserRepositoryFullModel

from src_v0.schemas.assistant import AssistantDTO

from src_v0.ai_communicator.gpt_comunicator import GptCommunicator
from src_v0.ai_communicator.model import AIAssistant
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.repository.storage import RepoStorage
from src_v0.services.openai_api_package.chat_gpt_package.client import GPTClient
from src_v0.services.openai_api_package.chat_gpt_package.model import GPTOptions


class OpenAiresponser:
    """
    Класс выполняет функцию общения
    отправляет запрос в ИИ получает и отправлет ответ клиенту

    """
    conversation_context = {}

    options = GPTOptions(api_key="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", model_name='gpt-4o', max_message_count=20, temperature=1,
                         max_return_tokens=1000)

    gpt_client = GPTClient(options=options)
    communicator = GptCommunicator(gpt_client=gpt_client)

    def __init__(self, repo: RepoStorage):
        self.settings = {}
        self.repo = repo

    # TODO сделать модель для контекста
    # TODO Сжедать формирование контекста на сторое репозитория или базы
    async def get_context(self, user_id) -> list:
        """
        взять сообщения пользователя
        взять сообщения ассистента
        соеденить в словарь

        :return:
        :param user_id:
        :return:
        """
        user_messages = await self.repo.message_repo.user.get_user_messages_by_user_telegram_id(telegram_id=user_id)
        assistant_messages = await self.repo.message_repo.assistant.get_all_assistent_messages_by_user_telegram_id(
            telegram_id=user_id)
        messages = [({"role": "user", "content": i.text}, i.created_at) for i in user_messages] + [
            ({"role": "assistant", "content": i.text}, i.created_at) for i in assistant_messages]
        sorted_messages = sorted(messages, key=lambda x: x[1])
        context = [i[0] for i in sorted_messages]
        return context

    async def get_assistant(self, assistant_id) -> AIAssistant:
        assistant = await self.repo.assistant_repo.get_assistant(assistant_id=assistant_id)
        # TODO Передаелать модели в соответсии с выдачей
        return AIAssistant(
            assistant=assistant.name,
            name=assistant.name,
            assistant_prompt=assistant.system_prompt,
            user_prompt=assistant.user_prompt,
        )

    async def get_assistant_by_research(self, research_id) -> AIAssistant:
        assistant = await self.repo.assistant_repo.get_assistant_by_research(research_id=research_id)
        # TODO Передаелать модели в соответсии с выдачей
        return AIAssistant(
            assistant=assistant.name,
            name=assistant.name,
            assistant_prompt=assistant.system_prompt,
            user_prompt=assistant.user_prompt,
        )

    async def get_hello_answer_from_gpt(self, research_id):
        assistant = await self.get_assistant_by_research(research_id=research_id)
        response = await self.communicator.send_response(text="Сгенерируй приветсвенно собщнеие ", assistant=assistant)
        return response

    async def one_message(self,user_prompt,system_prompt):
        response = await self.communicator.send_one_message(user_prompt=user_prompt, system_prompt=system_prompt)
        return response

    # TODO Оптимизировать каждый раз загружать асситсентов не хопошо
    # TODO Поменять данные
    async def talk_to_gpt(self, user_id, research_id):
        assistant = await self.get_assistant_by_research(research_id=research_id)
        context = await self.get_context(user_id=user_id)
        response = await self.communicator.send_context(context=context, assistant=assistant)
        print()
        assistan_message = {"text": response,
                            "chat_id": 1,
                            "to_user_id": user_id,
                            "assistant_id": 1,
                            "telegram_client_id": 1}
        await self.repo.message_repo.assistant.save_new_message(values=assistan_message)
        return response


if __name__ == '__main__':
    async def main():
        storage = RepoStorage(database_session_manager=DatabaseSessionManager(
            database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))
        c = OpenAiresponser(repo=storage)
        asi = await c.get_context(user_id=2)
        print(asi)


    if __name__ == '__main__':
        asyncio.run(main())
