import asyncio

from loguru import logger
from pyrogram.raw.base import RpcError
from telethon import TelegramClient
from telethon.errors import ChatWriteForbiddenError
from telethon.errors import FloodWaitError
from telethon.errors import PeerFloodError
from telethon.errors import UserDeactivatedBanError

from configs.nats_queues import nats_subscriber_researcher_settings
from src.database.repository.storage import RepoStorage
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.services.exceptions.telegram_clients import AllClientsBannedError
from src.services.publisher.publisher import NatsPublisher


class ClientBanPublisher:
    def __init__(
            self,
            publisher: NatsPublisher
    ):
        self._publisher = publisher

    async def publish_ban_on_research(
            self,
            research_id: int
    ) -> None:
        await self._publish(
            subject=nats_subscriber_researcher_settings.researches.ban_telegram_research,
            research_id=research_id
        )
        logger.info(f"Account is banned. Message will not be sent for client with research_id: {research_id}.")

    async def publish_unban_research(
            self,
            research_id: int
    ) -> None:
        await self._publish(
            subject=nats_subscriber_researcher_settings.researches.unban_telegram_research,
            research_id=research_id
        )

        logger.info(f"Account is unbanned. Message will be sent for client with research_id: {research_id}.")

    async def _publish(
            self,
            subject: str,
            research_id: int,
    ) -> None:
        logger.debug(f"Publishing message to subject: {subject}")

        await self._publisher.publish_message_to_subject(
            subject_message=NatsQueueMessageDTOSubject(
                message="",
                subject=subject,
                headers={
                    "research_id": str(research_id),
                }
            )
        )


class ClientBanChecker:
    def __init__(
            self,
            publisher: NatsPublisher,
            repository: RepoStorage
    ):
        self.publisher = ClientBanPublisher(publisher=publisher)
        self._repository = repository

        self._tasks = {} # В дальнейшем через этот словарь можно чекать какие бан чекеры запущены

    async def start_check_ban(
            self,
            client: TelegramClient,
            research_id: int
    ) -> None:
        """
        Запускает задачу для проверки статуса бана аккаунта раз в час.
        """
        if client in self._tasks:
            logger.warning(f"Ban check already running for client: {client}")
            return

        logger.info(f"Starting ban check for client: {client} with research_id: {research_id}")

        client_info = await client.get_me()
        await self._repository.client_repo.update(
            telegram_client_id=client_info.id,
            values={
                "is_banned": True
            }
        )

        task = asyncio.create_task(
            self._periodic_check(
                research_id=research_id,
                client=client
            )
        )
        self._tasks[client] = task
        logger.info(f"Started ban check for client: {client}")


    @staticmethod
    async def check_is_account_banned(
            client: TelegramClient
    ) -> bool:
        """
         Проверяет статус аккаунта в @SpamBot. Возвращает False, если аккаунт не заблокирован, иначе True.
         """

        try:
            logger.info("Checking account status via @SpamBot")
            async with client.conversation("@SpamBot") as conv:
                await conv.send_message("/start")
                response = await conv.get_response()
                if "no limits are currently" in response.text.lower():
                    logger.info("Account is not banned.")
                    return False
                elif "restricted" in response.text.lower():  # что тут должно быть
                    logger.warning("Account is restricted.")
                else:
                    logger.error("Unknown response from @SpamBot.")
                return True

        except (UserDeactivatedBanError, ChatWriteForbiddenError, PeerFloodError) as e:
            logger.error(f"Аккаунт полностью заблокирован! Ошибка: {e} ")
            return True

        except FloodWaitError as e:
            logger.warning(f"Telegram временно ограничил отправку сообщений. Подождите {e.seconds} секунд.")
            await asyncio.sleep(e.seconds)
            return True

        except RpcError as e:
            logger.error(f"Ошибка RPC при проверке через @SpamBot: {e}")
            return True

        except Exception as e:
            logger.error(f"Failed to check account status: {e}")
            return True

    async def stop_check_ban(
            self,
            client: TelegramClient,
            research_id: int
    ) -> None:
        """
        Останавливает задачу проверки статуса бана для указанного клиента.
        """
        client_info = await client.get_me()
        logger.info(f"Stopping ban check for client: {client_info.username}")

        if client not in self._tasks:
            logger.warning(f"No ban check running for client: {client_info.username}")
            return

        try:
            if await self._check_is_publish_unban_research(research_id=research_id):
                await self.publisher.publish_unban_research(research_id=research_id)

        except AllClientsBannedError:
            logger.error(f"Что-то пошло не так.")

        await self._repository.client_repo.update(
            telegram_client_id=client_info.id,
            values={
                "is_banned": False
            }
        )

        task = self._tasks.pop(client)
        task.cancel()

        logger.info(f"Stopped ban check for client: {client}")

    async def _check_is_publish_unban_research(
            self,
            research_id: int
    ) -> bool:
        """
        Checks whether all clients associated with a given research_id are banned.
        Returns True if all clients are banned, otherwise False.
        """
        clients = await self._repository.client_repo.get_clients_by_research_id(
            research_id=research_id
        )
        return all(client.is_banned for client in clients)

    async def _periodic_check(
            self,
            client: TelegramClient,
            research_id: int
    ):

        while await self.check_is_account_banned(client=client):
            client_info = await client.get_me()
            logger.info(f"Client {client_info.username} is banned.")
            config = await self._repository.configuration_repo.get()
            await asyncio.sleep(config.ban_check_interval_in_minutes * 60)

        logger.info(f"Client {client} is unbanned.")
        await self.stop_check_ban(
            research_id=research_id,
            client=client
        )
