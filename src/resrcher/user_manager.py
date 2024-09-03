import asyncio
import datetime
from datetime import date

from faststream.nats import NatsBroker

from datasourse_for_test.resercch_imirtation import UserResearch

from src.database.database_t import comon_database as reserch_database
from src.resrcher.user_cimmunication import send_first_message


# TODO бесконечный цикл или цикл по завершению всех в прогресс?
class UserManager:

    def __init__(self, settings):
        self.settings = settings

    async def ping_users(self):
        # TODO Добавить возмодность условия пинга на реакцию если есть реакция или нет
        '''Пингует пользователей, у которых прошло определенное время с момента последнего сообщения от бота'''

        conditions = {
            "first": datetime.timedelta(minutes=1),
            "second": datetime.timedelta(minutes=2),
            "last": datetime.timedelta(minutes=3),
        }
        # Здесь следует получить настоящее время последнего сообщения пользователя из базы данных
        # (здесь используется datetime.datetime.now() - datetime.timedelta(minutes=1) для примера)
        user_last_message_time = datetime.datetime.now() - datetime.timedelta(minutes=1)

        while True:
            # Предполагается, что user_in_progress содержит ID пользователей, состояние которых нужно проверить
            user_ids = reserch_database.data['user_in_progress']

            for user_id in user_ids:
                print(f"Последнее сообщение пользователя {user_id} было в: {user_last_message_time}")
                time_delta = datetime.datetime.now() - user_last_message_time
                print(f"Прошло времени: {time_delta}")

                # Получаем текущее состояние пинга пользователя
                user_ping_status = reserch_database.data.get('ping_status', {}).get(user_id,
                                                                                    {"first": False, "second": False,
                                                                                     "last": False})

                # Проверки времени и обновление статусов пинга
                if time_delta < conditions["first"]:
                    # Сброс состояния пинга, если время меньше первой границы
                    user_ping_status = {"first": False, "second": False, "last": False}

                if conditions["first"] <= time_delta < conditions["second"] and not user_ping_status["first"]:
                    user_ping_status['first'] = True
                    print(f"Пинг через 1 минуту пользователь {user_id}")
                elif conditions["second"] <= time_delta < conditions["last"] and not user_ping_status["second"]:
                    user_ping_status['second'] = True
                    print(f"Пинг через 2 минуты пользователь {user_id}")
                elif time_delta >= conditions["last"] and not user_ping_status["last"]:
                    user_ping_status['last'] = True
                    print(f"Пинг через 3 минуты пользователь {user_id}")

                # Обновляем состояние пинга пользователя в базе данных
                reserch_database.data.setdefault('ping_status', {})[user_id] = user_ping_status

            # Перепроверка списка пользователей каждый цикл
            await asyncio.sleep(1)

    async def set_all_user_status_done(self, research_id):
        research: UserResearch = reserch_database.get(name=research_id)
        # всех пользователей их ин прогрес для этого иследования в доне
        if len(reserch_database.data['user_in_progress']) != 0:
            for user in reserch_database.data['user_in_progress']:
                reserch_database.data['user_in_progress'].remove(user)
        return True

    async def collect_user_information(self):
        """
        Собирает информацию о пользщователе
        :return:
        """
        ...

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
