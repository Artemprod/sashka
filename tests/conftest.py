from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
import json
from datetime import datetime
import pytest
from sqlalchemy import insert, text


from configs.database import database_postgres_settings

from src.database.postgres import (
    AssistantMessage,
    UserMessage,
    ModelBase,
    Assistant,
    TelegramClient,
    UserResearch,
    PingPrompt,
    Research,
    ResearchOwner,
    Services,
    UserStatus,
    ResearchStatus,
    User, Configuration,
)
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage





@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    session = DatabaseSessionManager(database_url=database_postgres_settings.async_postgres_url)

    async with session.engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.drop_all)
        await conn.run_sync(ModelBase.metadata.create_all)
        await conn.execute(text("ALTER TABLE user_research DROP CONSTRAINT IF EXISTS user_research_user_id_key"))
        await conn.commit()

    def open_mock_json(model: str):
        moc_file_path = Path(__file__).parent.joinpath("mock_models").joinpath(f"mock_{model}.json")
        with open(moc_file_path, "r") as file:
            return json.load(file)


    users = open_mock_json(model="user")
    research_owners = open_mock_json(model="research_owner")
    services = open_mock_json(model="services")
    telegram_clients = open_mock_json(model="client")
    researches = open_mock_json(model="research")
    assistants = open_mock_json(model="assistants")
    user_status = open_mock_json(model="user_status")
    research_statuses = open_mock_json(model="research_status")
    ping_promts = open_mock_json(model="ping")
    user_research = open_mock_json(model="user_research_relation")
    user_messages = open_mock_json(model="user_messages")
    assistants_messages = open_mock_json(model="assistant_message")
    configs = open_mock_json(model="configurations")

    if configs["created_at"]:
        configs["created_at"] = datetime.strptime(configs["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")


    for user in users:
        if user["last_online_date"]:
            user["last_online_date"] = datetime.strptime(user["last_online_date"], "%Y-%m-%dT%H:%M:%S")
        if user["created_at"]:
            user["created_at"] = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%S")

    # Преобразование дат в research_owners
    for research_owner in research_owners:
        if research_owner["last_online_date"]:
            research_owner["last_online_date"] = datetime.strptime(
                research_owner["last_online_date"], "%Y-%m-%dT%H:%M:%S"
            )
        if research_owner["created_at"]:
            research_owner["created_at"] = datetime.strptime(research_owner["created_at"], "%Y-%m-%dT%H:%M:%S")

    # Преобразование дат в telegram_clients
    for telegram_client in telegram_clients:
        if telegram_client["created_at"]:
            telegram_client["created_at"] = datetime.strptime(telegram_client["created_at"], "%Y-%m-%dT%H:%M:%S")

    # Преобразование дат в researches
    for research in researches:
        if research["start_date"]:
            research["start_date"] = datetime.strptime(research["start_date"], "%Y-%m-%dT%H:%M:%S")
        if research["end_date"]:
            research["end_date"] = datetime.strptime(research["end_date"], "%Y-%m-%dT%H:%M:%S")
        if research["created_at"]:
            research["created_at"] = datetime.strptime(research["created_at"], "%Y-%m-%dT%H:%M:%S")
        if research["updated_at"]:
            research["updated_at"] = datetime.strptime(research["updated_at"], "%Y-%m-%dT%H:%M:%S")

    # Преобразование дат в assistants
    for assistant in assistants:
        if assistant["created_at"]:
            assistant["created_at"] = datetime.strptime(assistant["created_at"], "%Y-%m-%dT%H:%M:%S")

    # Преобразование дат в user_status
    for status in user_status:
        if status["created_at"]:
            status["created_at"] = datetime.strptime(status["created_at"], "%Y-%m-%dT%H:%M:%S")
        if status["updated_at"]:
            status["updated_at"] = datetime.strptime(status["updated_at"], "%Y-%m-%dT%H:%M:%S")

    # Преобразование дат в research_statuses
    for status in research_statuses:
        if status["created_at"]:
            status["created_at"] = datetime.strptime(status["created_at"], "%Y-%m-%dT%H:%M:%S")
        if status["updated_at"]:
            status["updated_at"] = datetime.strptime(status["updated_at"], "%Y-%m-%dT%H:%M:%S")

    # Преобразование дат в ping_promts
    for prompt in ping_promts:
        if prompt["created_at"]:
            prompt["created_at"] = datetime.strptime(prompt["created_at"], "%Y-%m-%dT%H:%M:%S")

    # Преобразование дат в user_research
    for relation in user_research:
        if relation["created_at"]:
            relation["created_at"] = datetime.strptime(relation["created_at"], "%Y-%m-%dT%H:%M:%S")

    # Преобразование дат в user_messages
    for message in user_messages:
        if message["created_at"]:
            message["created_at"] = datetime.strptime(message["created_at"], "%Y-%m-%dT%H:%M:%S")

    # Преобразование дат в assistants_messages
    for message in assistants_messages:
        if message["created_at"]:
            message["created_at"] = datetime.strptime(message["created_at"], "%Y-%m-%dT%H:%M:%S")

    async with session.async_session_factory() as session:
        add_users = insert(User).values(users)
        add_service = insert(Services).values(services)
        add_research_owner = insert(ResearchOwner).values(research_owners)
        add_telegram_client = insert(TelegramClient).values(telegram_clients)
        add_researches = insert(Research).values(researches)
        add_assistants = insert(Assistant).values(assistants)
        add_user_status = insert(UserStatus).values(user_status)
        add_ping_promts = insert(PingPrompt).values(ping_promts)
        add_research_statuses = insert(ResearchStatus).values(research_statuses)
        add_user_research = insert(UserResearch).values(user_research)
        add_user_messages = insert(UserMessage).values(user_messages)
        add_assistants_messages = insert(AssistantMessage).values(assistants_messages)
        add_configs = insert(Configuration).values(configs)

        await session.execute(add_users)
        await session.execute(add_service)
        await session.execute(add_assistants)

        await session.execute(add_research_owner)
        await session.execute(add_telegram_client)
        await session.execute(add_researches)
        await session.execute(add_user_status)
        await session.execute(add_ping_promts)
        await session.execute(add_research_statuses)
        await session.execute(add_user_research)
        await session.execute(add_user_messages)
        await session.execute(add_assistants_messages)
        await session.execute(add_configs)

        await session.commit()


@pytest.fixture(scope="session", autouse=True)
async def load_database_session() -> DatabaseSessionManager:
    return DatabaseSessionManager(database_url=database_postgres_settings.async_postgres_url)


@pytest.fixture(scope="session", autouse=True)
async def load_repository(load_database_session) -> RepoStorage:
    return RepoStorage(database_session_manager=load_database_session)


@pytest.fixture(scope="session", autouse=True)
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

