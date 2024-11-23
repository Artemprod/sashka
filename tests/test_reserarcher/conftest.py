import asyncio
import datetime

import faker
import pytest

from configs.database import test_database_postgres_settings
from src.database.postgres import ModelBase, Services, User, ResearchStatusEnum, UserStatusEnum, ResearchOwner, \
    Research, ResearchStatus, UserStatus
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.client import ClientRepository
from src.database.repository.storage import RepoStorage
from src.schemas.service.assistant import AssistantDTOPost
from src.schemas.service.client import TelegramClientDTOPost
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.inspector import ResearchStopper

fake = faker.Faker()


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine(event_loop):
    engine = DatabaseSessionManager(database_url=test_database_postgres_settings.async_postgres_url)
    event_loop.stop()
    yield engine
    await engine.engine.dispose()


@pytest.fixture(scope="session")
async def init_db(db_engine) -> DatabaseSessionManager:
    async def create_tables():
        """Создать все таблицы в базе данных."""
        async with db_engine.engine.begin() as conn:
            await conn.run_sync(ModelBase.metadata.create_all)

    async def drop_tables():
        """Удалить все таблицы в базе данных."""
        async with db_engine.engine.begin() as conn:
            await conn.run_sync(ModelBase.metadata.drop_all)

    await drop_tables()
    await create_tables()
    yield db_engine
    # await drop_tables()


@pytest.fixture(scope="session")
async def _repo_storage(init_db):
    yield RepoStorage(init_db)


@pytest.fixture(scope="session")
async def create_test_data(init_db, _repo_storage):
    # Create Assistant
    assistants = AssistantDTOPost(
        name="Test Assistant", system_prompt="Test System Prompt",
        user_prompt="Test User Prompt", for_conversation=True
    )
    await _repo_storage.assistant_repo.save_new_assistant(assistants.dict())

    # Create TelegramClient
    telegram_client = TelegramClientDTOPost(
        telegram_client_id=123456789,  # Уникальный ID клиента
        name="Test Client",
        api_id="12345",  # Тестовый API ID
        api_hash="abc123hash",  # Тестовый API Hash
        app_version="1.0.0",
        device_model="TestDevice",
        system_version="TestOS 1.0",
        lang_code="ru",
        test_mode=True,
        session_string="1Appwlasjdfks-askdjfkasj-",
        phone_number="892520293",
        password="892520293",
        parse_mode="html",
        workdir="/tmp/test_client",
        created_at=datetime.datetime.utcnow()
    )
    await _repo_storage.client_repo.save(telegram_client.dict())

    # Create Service
    async with init_db.async_session_factory() as session:
        async with session.begin():
            # Создаем тестовый сервис
            service = Services(service_id=1, name="Test Service")
            session.add(service)
            await session.commit()

    # Create ResearchOwner
    async with init_db.async_session_factory() as session:
        async with session.begin():
            research_owner = ResearchOwner(
                name=fake.first_name(),
                second_name=fake.last_name(),
                phone_number=fake.phone_number(),
                service_owner_id=fake.random_int(min=1000, max=9999),
                tg_link=f"https://t.me/{fake.user_name()}",
                last_online_date=fake.date_time_between(start_date='-30d', end_date='now'),
                language_code="en",
                created_at=datetime.datetime.utcnow(),
                service_id=service.service_id
            )
            session.add(research_owner)
            await session.commit()

    # Create Users
    async with init_db.async_session_factory() as session:
        async with session.begin():
            users = [
                User(
                    tg_user_id=fake.random_int(min=100000000, max=999999999),
                    username=fake.user_name(),
                    name=fake.first_name(),
                    second_name=fake.last_name(),
                    phone_number=fake.phone_number(),
                    tg_link=f"https://t.me/{fake.user_name()}",
                    is_verified=fake.boolean(),
                    is_scam=fake.boolean(),
                    is_fake=fake.boolean(),
                    is_premium=fake.boolean(),
                    last_online_date=fake.date_time_between(start_date='-30d', end_date='now'),
                    language_code=fake.language_code(),
                    is_info=fake.boolean(),
                    created_at=datetime.datetime.utcnow()
                ) for _ in range(5)
            ]
            session.add_all(users)
            await session.commit()

    # Create Research
    async with init_db.async_session_factory() as session:
        async with session.begin():
            # Создаем исследования
            researches = [
                Research(
                    research_id=i,
                    research_uuid=fake.uuid4(),
                    owner_id=research_owner.owner_id,
                    name=f"Research {i}",
                    title=f"Title {i}",
                    theme=f"Theme {i}",
                    start_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
                    end_date=datetime.datetime.utcnow() + datetime.timedelta(days=30),
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow(),
                    descriptions=fake.text(),
                    additional_information=fake.text(),
                    assistant_id=1,  # Заполните при необходимости
                    telegram_client_id=1  # Заполните при необходимости
                ) for i in range(1, 4)
            ]
            session.add_all(researches)
            await session.commit()

    # Create Research Status
    async with init_db.async_session_factory() as session:
        async with session.begin():
            for i in range(len(researches)):
                research_status = ResearchStatus(
                    research_id=researches[i].research_id,
                    status_name=ResearchStatusEnum.WAIT,
                    updated_at=datetime.datetime.utcnow()
                )
                session.add(research_status)
            await session.commit()

    # Create User Status
    async with init_db.async_session_factory() as session:
        async with session.begin():
            user_status = [
                UserStatus(
                    user_id=users[i].user_id,
                    status_name=UserStatusEnum.WAIT,
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow()
                ) for i in range(len(users))
            ]
            session.add_all(user_status)
            await session.commit()

    async with init_db.async_session_factory() as session:
        async with session.begin():
            for i in range(len(users)):
                await _repo_storage.user_in_research_repo.short.bind_research(
                    user_id=users[i].user_id,
                    research_id=researches[0].research_id
                )
            await session.commit()

    print("Тестовые данные успешно созданы!")


@pytest.fixture(scope="session")
def repo_storage(init_db, create_test_data):
    yield RepoStorage(init_db)


@pytest.fixture(scope="session")
def research_stopper(repo_storage):
    yield ResearchStopper(repo_storage, notifier=None)


@pytest.fixture(scope="session")
async def publisher():
    yield NatsPublisher()
