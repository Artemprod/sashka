import asyncio
import datetime
import math
import random
from datetime import date

import tzlocal
from faststream.nats import NatsBroker

from datasourse_for_test.resercch_imirtation import UserResearch
from src_v0.ai_communicator.gpt_comunicator import GptCommunicator
from src_v0.database.connections.redis_connect import RedisPing

from src_v0.database.database_t import comon_database as reserch_database
from src_v0.database.postgres.models.enum_types import UserStatusEnum
from src_v0.database.postgres.models.message import AssistantMessage
from src_v0.database.postgres.t_data_objects import example_users
from src_v0.database.repository.storage import RepoStorage
from src_v0.resrcher.open_ai_namager import OpenAiresponser
from src_v0.schemas.user import UserDTO


# TODO бесконечный цикл или цикл по завершению всех в прогресс?
# TODO Проблема в высчитывании тайм дельты и условии которое сбрасывает флаги подумать над системой отслеживания оповещений 
class UserManager:
    max_pings = 4
    ping_attempts = 20

    def __init__(self, repo: RepoStorage,

                 settings=None):
        self.settings = settings
        self.repo = repo
        self.ai_responser = OpenAiresponser(repo=self.repo)


    # TODO не забудб что тут User это модель ORM
    async def ping_users(self, research_id):
        """Пинг пользователей до тех пор, пока есть активные пользователи."""
        # TODO вощможно стоит подумать над тем как управлять циклам до каких пор делать пинг ?
        while True:
            users = await self.get_active_users(research_id)

            if not users:  # Если нет активных пользователей, выходим из цикла
                print("Все пользователи завершили задачи. Остановка пинга.")
                break
            # Обрабатываем пинг для всех пользователей одновременно
            await asyncio.gather(*[self.handle_user_ping(user) for user in users])
            await asyncio.sleep(1)  # Задержка перед следующим пингом

    async def get_active_users(self, research_id):
        """Получение пользователей со статусом IN_PROGRESS."""
        return await self.repo.status_repo.user_status.get_users_by_research_with_status(
            research_id=research_id,
            status=UserStatusEnum.IN_PROGRESS
        )

    async def handle_user_ping(self, user):
        """Проверка времени последнего сообщения и выполнение пинга.
        если не 0 то дальше по логике
        """
        print("_____________users", user.user_id)
        unresponed_messages = await self.count_unresponed_assistant_message(user.tg_user_id)
        print("_____________unresponed_messages", unresponed_messages, "_______ user_id", user.user_id)
        if unresponed_messages == 0:
            return

        if unresponed_messages > UserManager.max_pings:
            print(f"Превышено максимальное количество пингов для пользователя {user.tg_user_id}.")
            return

        time_delay = self.calculate_ping_delay(unresponed_messages)
        print("_____________time_delay", time_delay, "_______ user_id", user.user_id)
        send_time = await self.calculate_send_data(telegram_id=user.tg_user_id, time_delay=time_delay)
        print("______________Время когда должно быть отправдено сообщение", send_time, "_______ user_id", user.user_id)
        #TODO решить вопрос с временными зонами (конверитровать серверное время или еще как то )
        current_time_utc = datetime.datetime.now(datetime.timezone.utc)
        # Если время отправки должно быть меньше или равно текущему времени в UTC
        if send_time <= current_time_utc:
            await self.send_ping_message(user=user, prompt_number=unresponed_messages)

    async def get_ping_prompt(self, number_of_message):
        message = await self.repo.ping_prompt_repo.get_ping_prompt_by_order_number(ping_order_number=number_of_message)
        return message

    async def count_unresponed_assistant_message(self, telegram_id) -> int:
        """Получение всех неотвеченых сообщений от ассистента."""
        unresponsed_assistant_messages = await self.repo.message_repo.assistant.fetch_assistant_messages_after_user(
            telegram_id=telegram_id)
        return len(unresponsed_assistant_messages)

    async def calculate_send_data(self, time_delay, telegram_id):
        #TODO сделайть управление локальной тайм зоной
        # Проблема в коныертации таймзоны в локальную на сервере время одно на компьютере другое

        last_user_message = await self.repo.message_repo.user.get_last_user_message_by_user_telegram_id(telegram_id)
        if last_user_message.created_at.tzinfo is None:
            # Если временная зона не указана — добавляем явную привязку к UTC
            last_message_time = last_user_message.created_at.replace(tzinfo=datetime.timezone.utc)
        else:
            last_message_time = last_user_message.created_at

            # Возвращаем время последнего сообщения с добавленной задержкой
        return last_message_time + datetime.timedelta(seconds=time_delay*10)


    def calculate_ping_delay(self, n) -> int | None:
        """
        Функция для вычисления задержки пинга на основе входного значения n.

        Аргументы:
        n (int): Входное число, для которого нужно рассчитать задержку.

        Возвращает:
        float: Рассчитанное значение задержки пинга.
        """
        if n < 0:
            print("Wrong input, n must be non-negative")
            return None  # Возвращаем None вместо пустого return

        elif n <= 3:
            # Используем math.factorial и math.sqrt для малых значений n
            delay = math.ceil(math.factorial(n + 1) - 1)
            return int(delay)

        else:
            # Логарифмическая функция для n > 3
            delay = math.ceil(10 * math.log(n) * (n - 3) + 24)
            return int(delay)

    async def send_ping_message(self, user, prompt_number):
        """Отправка пинг-сообщения."""
        prompt_object = await self.get_ping_prompt(number_of_message=prompt_number)

        message = await self.ai_responser.one_message(user_prompt=prompt_object.prompt,
                                                      system_prompt=prompt_object.system_prompt)
        assistan_message = {"text": message,
                            "chat_id": 1,
                            "to_user_id": user.tg_user_id,
                            "assistant_id": 1,
                            "telegram_client_id": 1}

        await self.repo.message_repo.assistant.save_new_message(values=assistan_message)
        headers = {
            'Tg-Client-Name': "cl",
            'Tg-User-UserId': str(user.tg_user_id),
        }

        try:
            async with NatsBroker() as broker:
                await broker.publish(
                    message=message,
                    subject="test.message.conversation.send",
                    stream="CONVERSATION",
                    headers=headers
                )
                print(f"Сообщение  успешно отправлено пользователю {user.tg_user_id}")
                print("______________Время реальной отправки сообщения",  datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None), "_______ user_id", user.user_id)

        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user.tg_user_id}: {e}")

    async def create_user_information(self, user_telegram_id):
        """
        Собирает информацию о пользщователе
        задача в очередь
        :return:
        """
        rand_user = random.choice(example_users)
        user = UserDTO(tg_user_id=user_telegram_id,
                       **rand_user)
        return user

    async def collect_users_information(self, user_telegram_ids: list[int]):
        """
        Собирает информацию о пользщователе
        задача в очередь
        :return:
        """
        users_dto = []
        for telegram_id in user_telegram_ids:
            user = await self.create_user_information(telegram_id)
            users_dto.append(user)
        return users_dto

    async def add_user(self, user_id, research_id):
        research: UserResearch = reserch_database.get(name=research_id)
        research.user_ids.append(int(user_id))
        print(f"user {user_id} appended")

    async def delete_user(self, user_id, research_id):
        research: UserResearch = reserch_database.get(name=research_id)
        research.user_ids.remove(int(user_id))
        print(f"user {user_id} deleted")

    async def change_user_status(self, user_id):
        reserch_database.data['user_in_progress'].remove(user_id)
        reserch_database.data['done'].append(user_id)
        print(f"Список пользователей в done  {reserch_database.data['done']}")
