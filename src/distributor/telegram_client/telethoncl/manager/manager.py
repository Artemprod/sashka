import datetime
from abc import ABC
from abc import abstractmethod
from typing import List
from typing import Optional

from loguru import logger
from telethon import TelegramClient
from telethon.errors import AuthKeyUnregisteredError
from telethon.errors import PhoneCodeInvalidError
from telethon.errors import PhoneNumberBannedError
from telethon.errors import RPCError
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from telethon.tl.types import User

from src.dispatcher.communicators.consol import ConsoleCommunicator
from src.dispatcher.communicators.reggestry import BaseCommunicator
from src.distributor.telegram_client.pyro.client.model import ClientConfigDTO
from src.distributor.telegram_client.telethoncl.exceptions.autrization import UserNotAuthorizedError
from src.distributor.telegram_client.telethoncl.exceptions.data import NoClientDataError
from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.client import TelegramClientDTOPost


class ClientStrategy(ABC):
    @abstractmethod
    async def execute(self, *args, **kwargs):
        pass


class SaveClientStrategy(ClientStrategy):
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, client_info: User, session_string: str, configs: ClientConfigDTO):
        client_dto = TelegramClientDTOPost(
            telegram_client_id=client_info.id,
            name=configs.name,
            api_id=str(configs.api_id),
            api_hash=str(configs.api_hash),
            app_version=configs.app_version,
            device_model=configs.device_model,
            system_version=configs.system_version,
            lang_code=configs.lang_code,
            test_mode=configs.test_mode,
            session_string=session_string,
            phone_number=configs.phone_number,
            password=configs.password,
            parse_mode=configs.parse_mode,
            workdir=configs.workdir,
            created_at=datetime.datetime.now()
        )
        try:
            new_client = await self.repository.client_repo.save(values=client_dto.dict())
            logger.info(f"New client saved: {client_dto.name}")
            return new_client
        except Exception as e:
            logger.error(f"Error saving client: {str(e)}")
            raise


class GetClientStrategy(ClientStrategy):
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, client_dto: TelegramClientDTOGet):
        try:
            if client_dto.client_id:
                return await self.repository.client_repo.get_client_by_id(client_id=client_dto.client_id)
            else:
                return await self.repository.client_repo.get_client_by_telegram_id(
                    telegram_id=client_dto.telegram_client_id)
        except Exception as e:
            logger.error(f"Error getting client: {str(e)}")
            raise


class CreateSessionStrategy(ClientStrategy):
    MAX_ATTEMPT = 5

    @staticmethod
    async def execute(client_configs: ClientConfigDTO, communicator: BaseCommunicator = ConsoleCommunicator()):
        string_session = StringSession()
        client = TelegramClient(
            string_session, int(client_configs.api_id),
            client_configs.api_hash,
            device_model=client_configs.device_model,
            system_version=client_configs.system_version,
            app_version=client_configs.app_version,
            lang_code=client_configs.lang_code,
            system_lang_code="en-US"
        )
        cloud_password = client_configs.password if client_configs.password else communicator.enter_cloud_password
        phone = client_configs.phone_number if client_configs.phone_number else communicator.enter_phone_number
        try:
            # noinspection PyTypeChecker
            await client.start(phone=phone,
                               password=cloud_password,
                               code_callback=communicator.get_code,
                               max_attempts=CreateSessionStrategy.MAX_ATTEMPT)
            user_client = await client.get_me()

            return string_session.save(), user_client
        except (PhoneCodeInvalidError, SessionPasswordNeededError, PhoneNumberBannedError) as e:
            logger.error(f"Error in session creation: {str(e)}")
            raise
        finally:
            await client.disconnect()


class RunClientStrategy(ClientStrategy):
    RETRY_DELAY = 10
    RECONNECTION_RETRIES = 10
    REQUEST_RETRIES = 10

    def __init__(self,
                 client_dto: TelegramClientDTOGet,
                 handlers: Optional[List] = None):

        self.client_dto = client_dto
        self.handlers = handlers or []
        self.client: Optional[TelegramClient] = None

    async def add_handlers(self):
        for handler in self.handlers:
            self.client.add_event_handler(handler)
        logger.info("All handlers added")

    async def execute(self):
        if not self.client_dto:
            raise NoClientDataError(message='client dto is empty')


        self.client = TelegramClient(
            StringSession(self.client_dto.session_string),
            int(self.client_dto.api_id),
            self.client_dto.api_hash,
            device_model=self.client_dto.device_model,
            system_version=self.client_dto.system_version,
            app_version=self.client_dto.app_version,
            lang_code=self.client_dto.lang_code,
            system_lang_code="en-US",
            request_retries=RunClientStrategy.REQUEST_RETRIES,
            connection_retries=RunClientStrategy.RECONNECTION_RETRIES,
            retry_delay=RunClientStrategy.RETRY_DELAY,
            auto_reconnect=True,
            raise_last_call_error=True,
        )
        try:
            await self.try_to_start_and_run()
        except (AuthKeyUnregisteredError, RPCError) as e:
            logger.error(f"Error during client run: {str(e)}")
            raise

        except UserNotAuthorizedError:
            raise

    async def try_to_start_and_run(self):
        if not self.client:
            raise ValueError("No client")

        await self.client.connect()
        if not self.client.is_connected():
            raise ValueError("Client failed to connect")

        if not await self.client.is_user_authorized():
            raise UserNotAuthorizedError

        try:
            logger.info("Client successfully connected")
            logger.info(f"Client started: {self.client_dto.name}")
            await self.add_handlers()
            await self.client.run_until_disconnected()

        except Exception as e:
            logger.error(f"faild to start client{e} ")
            raise e


class TelethonManager:
    def __init__(self, repository,
                 client_configs: ClientConfigDTO):
        self.repository = repository
        self.client_configs = client_configs
        self.save_strategy = SaveClientStrategy(repository)
        self.get_strategy = GetClientStrategy(repository)
        self.session_strategy = CreateSessionStrategy()
        self.run_strategy: Optional[RunClientStrategy] = None
        self.saved_client: Optional[TelegramClientDTOGet] = None
        self.handlers: List = []  # Initialize handlers list


    async def new_client(self, communicator: BaseCommunicator = ConsoleCommunicator()):
        try:
            session_string,user = await self.session_strategy.execute(self.client_configs, communicator)
            self.saved_client = await self.save_strategy.execute(user, session_string, self.client_configs)
            logger.info(f"New client created and saved: {self.saved_client.name}")

        except (PhoneNumberBannedError, SessionPasswordNeededError, PhoneCodeInvalidError, RPCError) as e:
            logger.error(f"Error during new client creation: {str(e)}")
            raise

    async def run(self):

        if self.saved_client is None:
            raise ValueError("No client to run. Call new_client() first.")

        self.run_strategy = RunClientStrategy(client_dto=self.saved_client, handlers=self.handlers)

        try:
            await self.run_strategy.execute()

        except UserNotAuthorizedError as e:
            raise e

        except AuthKeyUnregisteredError as e:
            logger.error(f"Error during client run: {str(e)}. Trying re-authentication.")
            await self.new_client()
            await self.run()


    async def stop_client(self):
        if self.run_strategy and self.run_strategy.client:
            await self.run_strategy.client.disconnect()
            logger.info(f"Client {self.saved_client.name} stopped")
        else:
            logger.warning("No active client to stop")

    def add_handlers(self, handlers: List):
        if handlers:
            self.handlers.extend(handlers)
            logger.info(f"{len(handlers)} handlers added to the internal list.")

            # Add handlers to the client if it is running
            if self.run_strategy and self.run_strategy.client and self.run_strategy.client.is_connected():
                for handler in handlers:
                    try:
                        self.run_strategy.client.add_event_handler(handler)
                        logger.info(f"Handler added to running client {self.saved_client.name}: {handler}")
                    except Exception as e:
                        logger.error(f"Failed to add handler {handler}: {str(e)}")
            else:
                logger.warning("Client not running. Handlers will be added when client starts.")
        else:
            logger.error("Attempted to add an empty list of handlers.")

