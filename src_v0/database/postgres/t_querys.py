import asyncio
import datetime
import math

import asyncpg
from sqlalchemy import select, func, cast, Integer, and_
from sqlalchemy.orm import aliased, selectinload, joinedload

from src.schemas.service.owner import ResearchOwnerDTO
from src.schemas.service.research import ResearchDTOPost
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.research.telegram.manager import TelegramResearchManager
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.postgres.models.assistants import Assistant
from src_v0.database.postgres.models.base import ModelBase
from src_v0.database.postgres.models.enum_types import ResearchStatusEnum, UserStatusEnum
from src_v0.database.postgres.models.many_to_many import UserResearch
from src_v0.database.postgres.models.research import Research
from src_v0.database.postgres.models.status import ResearchStatus, UserStatus

from src_v0.database.postgres.models.user import User
from src_v0.database.postgres.t_data_objects import users_list, clients, user_message, voice_message, assistant_message, \
    user_research, user_statuses, research_statuses, assistant_list, reserches_list, research_owner, service, \
    ping_prompt
from src_v0.database.repository.owner import ResearchOwnerRepositoryFullModel
from src_v0.database.repository.storage import RepoStorage
# from src_v0.resrcher.resercher import TelegramResearcher
from src_v0.schemas.assistant import AssistantDTO

session = DatabaseSessionManager(database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client')


async def drop_tables():
    async with session.engine.begin() as connection:
        await connection.run_sync(ModelBase.metadata.drop_all)


async def create_tables():
    async with session.engine.begin() as connection:
        await connection.run_sync(ModelBase.metadata.create_all)


async def load_data():
    async with session.async_session_factory() as coonection:
        coonection.add_all(ping_prompt)
        coonection.add(service)
        coonection.add(research_owner)
        coonection.add_all(clients)

        await coonection.commit()
        coonection.add_all(users_list)
        coonection.add_all(assistant_list)
        coonection.add_all(clients)
        coonection.add_all(reserches_list)
        coonection.add_all(user_message)
        coonection.add_all(voice_message)
        coonection.add_all(assistant_message)

        await coonection.commit()
        coonection.add_all(user_statuses)
        coonection.add_all(research_statuses)
        coonection.add_all(user_research)
        await coonection.commit()


async def count_user_by_language(like_sername: str = "D"):
    """

    SELECT
        language_code,
        count(language_code)::INT as count_all
    FROM public.users
    WHERE second_name LIKE 'D%' and phone_number LIKE '%12%'
    GROUP BY language_code
    """
    async with session.async_session_factory() as connection:
        query = (
            select(
                User.language_code,
                cast(func.count(User.language_code), Integer).label("count_all"),
            )
            .select_from(User)
            .filter(and_(User.second_name.contains(like_sername),
                         User.phone_number.contains(12),
                         ))
            .group_by(User.language_code)
        )
        print(query.compile(compile_kwargs={"literal_binds": True}))
        res = await connection.execute(query)
        result = res.all()
        print(result[0].count_all)
        print(result)


async def user_by_country_in_research(country_code: str = 'es'):
    """
    WITH condition_halper AS
    	-- основной запрос
    	(SELECT
    		user_name,
    		language_code,
    		r.name as research_name,
    		r.owner as owner,
    		r.theme as theme

    	FROM
    		--sub 1 таблица пользоватлеь - иследование
    		(SELECT u.name as user_name,
    				u.language_code as language_code,
    				u_r.research_id as research_id
    		FROM public.users as u
    		JOIN public.user_research as u_r ON u.user_id=u_r.user_id) as user_reserch_con

    	JOIN public.researches as r ON user_reserch_con.research_id=r.research_id)

    SELECT * FROM condition_halper WHERE language_code = 'es'
    """
    async with session.async_session_factory() as connection:
        u = aliased(User)
        r = aliased(Research)
        u_r = aliased(UserResearch)

        sub = (
            select(
                u.name.label("user_name"),
                u.language_code.label("language_code"),
                u_r.research_id.label("research_id"),

            )
            .select_from(u)
            .join(u_r, u_r.user_id == u.user_id).subquery("user_reserch_con")
        )
        cte = (
            select(
                sub.c.user_name,
                sub.c.language_code,
                r.name.label("research_name"),
                r.owner.label("owner"),
                r.theme.label("theme")
            )
            .join(r, r.research_id == sub.c.research_id)
            .cte("condition_halper")
        )
        query = (
            select(cte)
            .where(cte.c.language_code.contains(country_code))
        )
        print(query.compile(compile_kwargs={"literal_binds": True}))
        res = await connection.execute(query)
        result = res.all()
        print(result)


async def reserch_co_and_greater_than_five(theme_like: str = 'co', count_user: int = 5):
    """
    Выборка иследований у которых имя 'co' и количесвто участников больше 5
    SELECT res.name,
            res.title,
            res.theme,
            res.start_date,
            res.end_date,
            count(us.name)::int

    FROM public.researches as res

        JOIN public.user_research as u_res
            ON res.research_id = u_res.research_id
        JOIN public.users as us
            ON  u_res.user_id = us.user_id

    WHERE res.theme like '%co%'
    GROUP BY res.name, res.title,res.theme,res.start_date,res.end_date
    HAVING count(us.name) > 5

    """

    async with session.async_session_factory() as connection:
        res = aliased(Research)
        u_r = aliased(UserResearch)
        us = aliased(User)

        query = (
            select(
                res.title,
                res.theme,
                res.start_date,
                res.end_date,
                cast(func.count(us.name), Integer).label("count_all"),
            )
            .select_from(res)
            .join(u_r, u_r.research_id == res.research_id)
            .join(us, u_r.user_id == us.user_id)
            .filter(res.theme.contains(theme_like))
            .group_by(res.title, res.theme, res.start_date, res.end_date)
            .having(func.count(us.name) > count_user)
        )

        print(query.compile(compile_kwargs={"literal_binds": True}))
        res = await connection.execute(query)
        result = res.all()
        print(result)


async def count_user_in_progres():
    """
    Считает сколько участников находится в статусе in progress
    SELECT COUNT(public.users.name),
    		public.user_status_name.status

    FROM public.users
    JOIN public.user_status
    ON public.users.user_id = public.user_status.user_id
    JOIN public.user_status_name
    ON public.user_status.status_id  = public.user_status_name.status_id
    WHERE public.user_status_name.status = 'IN_PROGRESS'
    GROUP BY public.user_status_name.status
    """
    async with session.async_session_factory() as coonection:
        query = (
            select(

            )
        )


async def just_te():
    """
        async def check_history(self, user_id: int, source: str) -> bool:
        async with self.db_session_manager.session_scope() as session:
            query = select(HistoryModel).filter(HistoryModel.user_id==user_id)
            query = select(HistoryModel). \
                filter(HistoryModel.user_id == user_id). \
                filter(HistoryModel.service_source == source)
            result = await session.execute(query)
            record = result.scalars().all()
            logger.info(f"Проверка ответа истории {len(record) > 0}")
            return len(record) > 0
    :return:
    filter(and_(HistoryModel.user_id == user_id,HistoryModel.service_source == source))
    """
    async with session.async_session_factory() as connection:
        query = (
            select(
                User
            ).filter(and_(User.language_code == "en", User.tg_user_id.contains(0)))
        )
        print(query.compile(compile_kwargs={"literal_binds": True}))
        res = await connection.execute(query)
        record = res.scalars().all()

        print(record)


async def selection_join():
    async with session.async_session_factory() as connection:
        query = (
            select(Research)
            .options(selectinload(Research.status),
                     selectinload(Research.users).options(selectinload(User.status)),
                     # selectinload(User.messages).options(
                     #     selectinload(UserMessage.voice_message)
                     )
            .options(joinedload(Research.assistant))
        )

        print(query.compile(compile_kwargs={"literal_binds": True}))
        res = await connection.execute(query)
        record = res.scalars().all()
        print(record)
        # statuses = record[0].statuses
        # print(statuses.status_id)


async def convert_to_dto():
    async with session.async_session_factory() as connection:
        query = (
            select(Assistant)
            .options(selectinload(Assistant.messages))
        )
        print(query.compile(compile_kwargs={"literal_binds": True}))
        res = await connection.execute(query)
        record = res.scalars().all()
        print(record)
        user_dto = [AssistantDTO.model_validate(row, from_attributes=True) for row in record]
        print(user_dto)


# async def new_research():
#     """
#             1. Получить данные об иследовании
#             2. Получить статус WAIT для иследования
#             3. Получить статус WAIT для пользователя
#             4. Привязать клиента
#             5. Привязать ассистента
#             6. Сохоанить данные в базу
#             7. Поставить статтус ожидания для иследования
#             8. Положить пользователей в базу данных
#             9. Поставить им статус ожидания
#             10. Привязать пользователй к иследованию
#
#             """
#
#     research = ResearchPost(
#         owner="Artem",
#         name="Инсайтер ",
#         title="Кастдев",
#         theme="Воволеченность пользщвоателей ",
#         description="То то то и это",
#         start_date=datetime.datetime.now(),
#         end_date=datetime.datetime(2024, 9, 3, 13, 0, 0),
#         additional_information="Какая то инфа дополнительная",
#         assistant_id=1,
#         users=[123, 321, 234, 566, 789, 345],
#     )
#     # User
#
#     async with session.async_session_factory() as connection:
#         # Получить Стаус ожидания
#         # Получить Ассистента
#
#         reserch_status_exec = await connection.execute(
#             select(ResearchStatus).filter(ResearchStatus.status_name == ResearchStatusEnum.WAIT)
#         )
#         reserch_status = reserch_status_exec.scalars().first()
#
#         user_status_exec = await connection.execute(
#             select(UserStatus).filter(UserStatus.status_name == UserStatusEnum.WAIT)
#         )
#         user_status = user_status_exec.scalars().first()
#
#         client_exec = await connection.execute(select(TelegramClient).filter(TelegramClient.telegram_client_id == 1))
#         client = client_exec.scalars().first()
#
#         reserch = Research(
#             owner=research.owner,
#             name=research.name,
#             title=research.title,
#             theme=research.theme,
#             start_date=research.start_date,
#             end_date=research.end_date,
#             descriptions=str(research.description),
#             additional_information=research.additional_information,
#             research_status_id=reserch_status.status_id,
#             assistant_id=research.assistant_id,
#             telegram_client_id=client.telegram_client_id
#
#         )
#         connection.add(reserch)
#
#         await connection.flush()
#
#
#         for user_id in research.users:
#             user = User(
#                 name="Unknown",
#                 tg_user_id=user_id,
#                 status_id=user_status.status_id,
#             )
#             connection.add(user)
#             await connection.flush()
#             user_r = UserResearch(
#                 user_id=user.user_id,
#                 research_id=reserch.research_id,
#             )
#             connection.add(user_r)
#         await connection.commit()
#     return reserch


async def start_research(reserch_id):
    """
    1. Поставить статус иследования на inprogres
    2. Всех пользователей превести в inprogres

    """
    async with session.async_session_factory() as connection:
        # Получить статусы исследования и пользователя IN_PROGRESS за один запрос
        research_status_exec = await connection.execute(
            select(ResearchStatus).filter(ResearchStatus.status_name == ResearchStatusEnum.IN_PROGRESS)
        )
        research_status = research_status_exec.scalars().first()

        user_status_exec = await connection.execute(
            select(UserStatus).filter(UserStatus.status_name == UserStatusEnum.IN_PROGRESS)
        )
        user_status = user_status_exec.scalars().first()

        # research = await new_research()

        research_exec = await connection.execute(
            select(Research)
            .filter(Research.research_id == 13)
            .options(selectinload(Research.users))
        )
        result = research_exec.scalars().first()
        result.research_status_id = research_status.status_id
        result.updated_at = datetime.datetime.now()

        for user in result.users:
            user.status_id = user_status.status_id
        await connection.commit()


async def stop_research(reserch_id=None):
    """
    1. Поставить статус иследования на DONE
    2. Всех пользователей если они есть  превести в DONE

    """
    async with session.async_session_factory() as connection:

        # Получить статусы исследования и пользователя IN_PROGRESS за один запрос
        research_status_exec = await connection.execute(
            select(ResearchStatus).filter(ResearchStatus.status_name == ResearchStatusEnum.DONE)
        )
        research_status = research_status_exec.scalars().first()

        user_status_exec = await connection.execute(
            select(UserStatus).filter(UserStatus.status_name == UserStatusEnum.DONE)
        )
        user_status = user_status_exec.scalars().first()

        # research = await new_research()

        research_exec = await connection.execute(
            select(Research)
            .filter(Research.research_id == 13)
            .options(selectinload(Research.users))
        )
        result = research_exec.scalars().first()
        result.research_status_id = research_status.status_id
        result.updated_at = datetime.datetime.now()
        if len(result.users) > 0:
            for user in result.users:
                user.status_id = user_status.status_id
        await connection.commit()


async def user_done(user_tg_id: int = 123):
    async with session.async_session_factory() as connection:
        user_status_exec = await connection.execute(
            select(UserStatus).filter(UserStatus.status_name == UserStatusEnum.DONE)
        )
        user_status = user_status_exec.scalars().first()

        user_exec = await connection.execute(
            select(User).filter(User.tg_user_id == user_tg_id)
        )
        user = user_exec.scalars().first()
        user.status_id = user_status.status_id
        await connection.commit()


async def user_wait(user_tg_id: int = 123):
    async with session.async_session_factory() as connection:
        user_status_exec = await connection.execute(
            select(UserStatus).filter(UserStatus.status_name == UserStatusEnum.WAIT)
        )
        user_status = user_status_exec.scalars().first()

        user_exec = await connection.execute(
            select(User).filter(User.tg_user_id == user_tg_id)
        )
        user = user_exec.scalars().first()
        user.status_id = user_status.status_id
        await connection.commit()





async def run_q():
    rep = ResearchOwnerRepositoryFullModel(db_session_manager=DatabaseSessionManager(
        database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))
    res = await rep.get_owner_by_id(owner_id=1)
    print(res)
    print()


def get_ping_message(msg):

    messages = {
        1: "Напоминание: Пожалуйста, ответьте на сообщение.",
        2: "Второе напоминание: Пожалуйста, ответьте на сообщение.",
        3: "Последнее напоминание: Пожалуйста, ответьте на сообщение.",
    }
    return messages[msg] if msg in messages else None


def get_ping_delay(n)-> int | None:
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



async def listen_for_notifications():

    conn = await asyncpg.connect(
            user='postgres',
            password='1234',
            database='cusdever_client',
            host='localhost',  # хост указывается отдельно
            port=5432  # порт указывается как отдельный параметр
     )
    def handle_notification(connection, pid, channel, payload):
        print(f"Получено уведомление из канала {channel}: {payload}")


    # Подписываемся на канал user_channel
    await conn.add_listener('user_channel', handle_notification)

    # Функция обратного вызова при получении уведомления


    print("Ожидание уведомлений...")
    while True:
        await asyncio.sleep(1)



async def first_run():
    # await drop_tables()
    await create_tables()
    await load_data()
def researc_ob():
    return ResearchDTOPost(
                owner_service_id=12343,
                research_uuid="123e4567-e89b-12d3-a456-426614174000",
                name="Test Research",
                title="Sample Test Title",
                theme="Science",
                start_date=datetime.datetime.now(),
                end_date=datetime.datetime.now() + datetime.timedelta(days=10),  # Конец исследования через 10 дней
                descriptions="This is a test research description",
                additional_information="This research is only for testing purposes",
                examinees_ids=[2200096081],
                assistant_id=1)



def owner_ob():
    return ResearchOwnerDTO(
        name="John Doe",
        service_owner_id=123,
        second_name="Smith",
        phone_number="+1234567890",
        tg_link="@johndoe",
        language_code="en",
        service_id=1
    )


async def t_research_creation():
    storage = RepoStorage(database_session_manager=DatabaseSessionManager(
        database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))
    # res = TelegramResearcher(research=research_im_1, repository=storage)
    t_manahger = TelegramResearchManager(research=researc_ob(),
                                         owner=owner_ob(),
                                         repository=storage,
                                         information_collector=TelegramUserInformationCollector())
    await t_manahger.create_research()

    # re = await storage.message_repo.assistant.fetch_assistant_messages_after_user(telegram_id=5000650204)

    # await storage.user_in_research_repo.short.change_status_one_user(telegram_id=1, status=UserStatusEnum.WAIT)
    # await storage.user_in_research_repo.short.change_status_group_of_user(user_group=[1,2,3], status=UserStatusEnum.WAIT)
    # record = await res.create_research()
    # await res.run_research()
    # print(record)
    # print()
    # cash = ResearchDataCashRepository(db_session_manager=DatabaseSessionManager(database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))
    # res = await cash.get_cash_information(research_id=20)
    # print()
    # u_m = UserManager(repo=storage)
    # await u_m.ping_users(research_id=3)
    # msg = get_ping_message(len(re))
    # delay = get_ping_delay(len(re))
    # delta = datetime.timedelta(hours=delay)
    # data = datetime.datetime.now() + delta
    # print()



if __name__ == '__main__':
    asyncio.run(load_data())

