import asyncio
import datetime

from loguru import logger
from telethon import TelegramClient

from configs.nats_queues import nats_subscriber_researcher_settings
from src.schemas.service.queue import NatsQueueMessageDTOSubject
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
            publisher: NatsPublisher
    ):
        self.publisher = ClientBanPublisher(publisher=publisher)

        self._tasks = {} # В дальнейшем через этот словарь можно чекать какие бан чекеры запущены

    async def start_check_ban(
            self,
            client: TelegramClient,
            research_id: int
    ) -> None:
        """
        Запускает задачу для проверки статуса бана аккаунта раз в час.
        """

        logger.info(f"Starting ban check for client: {client} with research_id: {research_id}")

        if client in self._tasks:
            logger.warning(f"Ban check already running for client: {client}")
            return

        await self.publisher.publish_ban_on_research(research_id=research_id)

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
        logger.info(f"Stopping ban check for client: {client}")
        if client not in self._tasks:
            logger.warning(f"No ban check running for client: {client}")
            return

        await self.publisher.publish_unban_research(research_id=research_id)

        task = self._tasks.pop(client)
        task.cancel()

        logger.info(f"Stopped ban check for client: {client}")

    async def _periodic_check(
            self,
            client: TelegramClient,
            research_id: int
    ):

        while await self.check_is_account_banned(client=client):
            logger.info(f"Client {client} is banned.")
            await asyncio.sleep(10)  # Проверка раз в час

        logger.info(f"Client {client} is unbanned.")
        await self.stop_check_ban(
            research_id=research_id,
            client=client
        )
