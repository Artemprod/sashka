import asyncio
from datetime import timedelta, datetime, timezone
from random import randint
from typing import Dict

from nats.js.api import PubAck

from datasourse_for_test.resercch_imirtation import UserResearch
from src_v0.ai_communicator.gpt_comunicator import GptCommunicator
from src_v0.ai_communicator.model import AIAssistant, assistant_aggressive, assistant_formal, \
    assistant_informal
from src_v0.database.database_t import comon_database as reserch_database
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.postgres.models.enum_types import UserStatusEnum
from src_v0.database.repository.storage import RepoStorage
from src_v0.resrcher.models import Headers, QUEUEMessage
from src_v0.resrcher.open_ai_namager import OpenAiresponser

from src_v0.services.openai_api_package.chat_gpt_package.client import GPTClient
from src_v0.services.openai_api_package.chat_gpt_package.model import GPTOptions

import asyncio
from faststream.nats import NatsBroker


class BaseCommunicator:
    ...


# TODO стоит ли коммуникатор создавать уже предуствановленым ( асистент , иследование и тд ) ответсвенный за создание коммуникатора иследователь ?
class Communicator(BaseCommunicator):
    """
    Класс выполняет функцию общения
    отправляет запрос в ИИ получает и отправлет ответ клиенту

    """

    def __init__(self, repo: RepoStorage, ai_responser: OpenAiresponser):
        self.settings = {
            "send_policy": 10,
            "delay_between_bunch": timedelta(seconds=5),
            "delay_between_messages": timedelta(seconds=1),
        }
        self.repo = repo
        self.ai_responser = ai_responser

    # TODO иследование поменять данные помсенть метод оптимизщировать
    async def answer_message(self, user_id, message):
        data = {
            "from_user": user_id,
            "chat": user_id,
            "media": False,
            "voice": False,
            "text": message,
        }
        await self.repo.message_repo.user.save_new_message(values=data)
        response = await self.ai_responser.talk_to_gpt(user_id=user_id, research_id=1)
        headers = {
            'Tg-Client-Name': str("cl"),
            'Tg-User-UserId': str(user_id),

        }
        async with NatsBroker() as broker:
            try:
                await broker.publish(
                    message=response,
                    subject="test.message.conversation.send",
                    stream="CONVERSATION",
                    headers=headers
                )
                print("Сообщение успешно опубликовано в очередь!")
                # TODO Сменить статус пользователя на IN PROGRESS
            except Exception as e:
                print(f"Ошибка при публикации сообщения: {e}")

    # TODO Вот тут логика отправки сообщений кусками генерируем сообщение кладем в чередь пачками

    async def send_first_message(self, resarch_id):
        """Делает первую рассылку по пользователем из изледования
        тот медот не знает о сущестоввании ИИ он только отправляет завпрос, получет ответ и перенаправлет в клиента
        Идея по реализации: использвоание jetstreem для рассылки через интервыал


        1. Получает данные о пользователи
            если есть лданные если нет
        2. получает ассистента
            еесли есть асистент если нет


        3. Отправлет запрос на отправку сообщение клинету
            - получить настройки для заджержки
            - получить списко польщовательских id
            для каждого id:
                - отправлет запрос к ИИ
                - Получает ответ
                    если есть ответ если нет ошибка
                - вычислить дату и время когда сообщение должно быть отправлено
                - заполнить хэжеры
                - сформировать сообщение
                - опудиковать в очередь стрим
                - получить подтверждение что все сообщения опудликованы
            если получилось отправить если нет ошибка


        """

        current_time = datetime.now(tz=timezone.utc)  # Текущее время
        # users = await self.repo.status_repo.user_status.get_users_by_research_with_status(research_id=resarch_id, status=UserStatusEnum.IN_PROGRESS)
        # user_ids = [i.user_id for i in users]
        user_ids = [1, 2, 3]

        people_per_day = self.settings.get("send_policy", 10)
        delay_between_bunch = self.settings.get("delay_between_bunch", timedelta(hours=24))
        telegram_client = await self.repo.client_repo.get_client_by_id(client_id=1)
        assistant = await self.repo.assistant_repo.get_assistant_by_research(research_id=resarch_id)
        right_border = 0

        for i, left_border in enumerate(range(0, len(user_ids), people_per_day)):
            if right_border + people_per_day > len(user_ids):
                right_border = len(user_ids)
            else:
                right_border = left_border + people_per_day
            print(f"_______GROUP__{i}________")
            for j, user in enumerate(user_ids[left_border:right_border]):
                next_time_message = current_time + (j * timedelta(seconds=randint(1, 2))) + (i * delay_between_bunch)

                print(f'User ID: {user}, Next Time Message: {next_time_message}')
                # Simulation of sending the message

                content = await self.ai_responser.get_hello_answer_from_gpt(research_id=resarch_id)

                headers = {
                    'Tg-Client-Name': str("cl"),
                    'Tg-User-UserId': str(user),
                    'SendTime-Msg-Timestamp': str(datetime.now(tz=timezone.utc).timestamp()),
                    'SendTime-Next-Message-Timestamp': str(next_time_message.timestamp()),
                }
                message = self.get_message(content=content, stream_name='WORK_QUEUE_4', headers=headers)

                async with NatsBroker() as broker:
                    try:
                        await broker.publish(
                            message=message.content,
                            subject=message.subject,
                            stream=message.stream,
                            headers=message.headers.dict(by_alias=True)
                        )
                        print("Сообщение успешно опубликовано в очередь!")
                        # TODO Вынести в модель DTO
                        # TODO Gjcnfdbnm chat_id опциональным
                        assistan_message = {"text": message.content,
                                            "chat_id": 1,
                                            "to_user_id": user,
                                            "assistant_id": assistant.assistant_id,
                                            "telegram_client_id": telegram_client.telegram_client_id}
                        await self.repo.message_repo.assistant.save_new_message(values=assistan_message)
                        # TODO Сменить статус пользователя на IN PROGRESS
                    except Exception as e:
                        print(f"Ошибка при публикации сообщения: {e}")

    def get_message(self, content: str, stream_name: str, headers):
        message = QUEUEMessage(
            content=content,
            subject="test_4.messages.send.first",
            stream=stream_name,
            headers=Headers(**headers)
        )
        return message

    # TODO вынести все работы со времен в класс работы со времени
    async def form_send_data(self):
        ...




async def main():
    storage = RepoStorage(database_session_manager=DatabaseSessionManager(
        database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))
    c = Communicator(repo=storage, ai_responser=OpenAiresponser(repo=storage))

    await c.send_first_message(resarch_id=41)


if __name__ == '__main__':
    asyncio.run(main())
