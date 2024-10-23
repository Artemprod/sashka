from enum import Enum
from typing import Optional, List, Union, Tuple

from environs import Env
from loguru import logger
from telethon import events
from telethon.tl.types import PeerUser, PeerChat, PeerChannel, User, Chat, Channel


class Filter:
    """Базовый фильтр с логикой обработки системных и ограниченных пользователей."""

    class SourceType(str, Enum):
        USER = "user"
        PRIVATE_CHAT = "chat"
        GROUP = "group"
        SUPERGROUP = "supergroup"
        CHANNEL = "channel"
        BOT = "bot"
        ANY = "any"

    TELEGRAM_SYSTEM_ACCOUNTS: List[Union[str, int]] = [
        "@PremiumBot", "@Telegram", "@PassportBot", "@GDPRbot",
        "@BotSupport", "@MTProxybot", "@DiscussBot", "@WebAppsBot",
        "@DurgerKingBot", "@BotFather", "@SpamBot", "@GameBot",
        "777000", "333000", "42777",
        "@QuizBot", "@TranslateBot", "@StoreBot", "@LotteryBot",
        "@GroupButler_bot", "@Stickers"
    ]

    RESTRICTED_USERS: Optional[List[Union[str, int]]] = []

    def __init__(self):
        logger.debug("Initializing Filter...")
        restricted_from_env = self._load_restricted_users()
        if not Filter.RESTRICTED_USERS:
            Filter.RESTRICTED_USERS = restricted_from_env
            logger.info("Initialized restricted users from environment.")
        else:
            new_users = set(restricted_from_env) - set(Filter.RESTRICTED_USERS)
            if new_users:
                Filter.RESTRICTED_USERS.extend(new_users)
                logger.info("Updated restricted users with new entries.")

    @staticmethod
    def _load_restricted_users() -> List[Union[str, int]]:
        env = Env()
        logger.debug("Loading restricted users from .env...")
        env.read_env('.env')
        try:
            users = list(env("NOT_ALLOWED_USERS", "").split(","))
            logger.debug(f"Loaded restricted users: {users}")
            return users
        except Exception as e:
            logger.error("Failed to load restricted users from .env: {}", e)
            raise e

    @classmethod
    def _add_restricted_users(cls, users: Union[List[Union[str, int]], str, int]) -> List[Union[str, int]]:
        logger.debug(f"Adding users to restricted list: {users}")
        if cls.RESTRICTED_USERS is None:
            cls.RESTRICTED_USERS = []

        try:
            if isinstance(users, list):
                cls.RESTRICTED_USERS.extend(users)
            elif isinstance(users, (str, int)):
                cls.RESTRICTED_USERS.append(users)
            else:
                logger.error("Invalid input type for restricted list.")
                raise ValueError("Invalid input type for restricted list.")

            logger.debug(f"Current restricted users list: {cls.RESTRICTED_USERS}")
            return cls.RESTRICTED_USERS
        except Exception as e:
            logger.error("Failed to add users to restricted list: {}", e)
            raise e

    def is_system_account(self, user: Union[str, int]) -> bool:
        result = str(user) in map(str, self.TELEGRAM_SYSTEM_ACCOUNTS)
        logger.debug(f"Checked if user {user} is system account: {result}")
        return result

    def is_restricted(self, user: Union[str, int]) -> bool:
        result = str(user) in map(str, self.RESTRICTED_USERS)
        logger.debug(f"Checked if user {user} is restricted: {result}")
        return result


class MediaFilter(Filter):
    """Фильтр для сообщений в зависимости от источника с поддержкой различных типов чатов."""

    SOURCE_TYPE_MAPPING = {
        Filter.SourceType.USER: PeerUser,
        Filter.SourceType.PRIVATE_CHAT: PeerUser,
        Filter.SourceType.GROUP: PeerChat,
        Filter.SourceType.SUPERGROUP: PeerChannel,
        Filter.SourceType.CHANNEL: PeerChannel,
        Filter.SourceType.BOT: PeerUser,
        Filter.SourceType.ANY: None
    }

    def __init__(self, source_type: Union[str, Filter.SourceType] = Filter.SourceType.ANY):
        logger.debug("Initializing MediaFilter...")
        super().__init__()
        if isinstance(source_type, str):
            source_type = Filter.SourceType(source_type.lower())

        self.source_type = source_type
        self.peer_type = self._load_source_type(self.source_type)
        logger.info(f"MediaFilter initialized with source_type={self.source_type}")

    def _load_source_type(self, source_type: Filter.SourceType):
        peer_type = self.SOURCE_TYPE_MAPPING.get(source_type)
        if peer_type is None and source_type != Filter.SourceType.ANY:
            logger.error(f"Unknown source type: {source_type}")
            raise ValueError(f"Unknown source type: {source_type}")

        logger.debug(f"Loaded peer type for source_type {source_type}: {peer_type}")
        return peer_type

    def _check_sender_restrictions(self, sender) -> bool:
        sender_id = sender.username or str(sender.id)
        result = not (self.is_system_account(sender_id) or self.is_restricted(sender_id))
        logger.debug(f"Checked sender restrictions for {sender_id}: {result}")
        return result

    def _validate_source_type(self, chat: Union[User, Chat, Channel]) -> bool:
        if self.source_type == self.SourceType.ANY:
            return True

        source_validators = {
            self.SourceType.BOT: lambda: isinstance(chat, User) and chat.bot,
            self.SourceType.SUPERGROUP: lambda: isinstance(chat, Channel) and chat.megagroup,
            self.SourceType.CHANNEL: lambda: isinstance(chat, Channel) and not chat.megagroup,
            self.SourceType.GROUP: lambda: isinstance(chat, Chat),
            self.SourceType.USER: lambda: isinstance(chat, User) and not chat.bot,
            self.SourceType.PRIVATE_CHAT: lambda: isinstance(chat, User) and not chat.bot,
        }

        validator = source_validators.get(self.source_type)
        result = validator() if validator else False
        logger.debug(f"Validated chat {chat} with source type {self.source_type}: {result}")
        return result

    @staticmethod
    async def _get_chat_and_sender(event: events.NewMessage) -> Tuple[
        Optional[Union[User, Chat, Channel]], Optional[User]]:
        logger.debug("Fetching chat and sender information...")
        try:
            chat = await event.get_chat() if hasattr(event, 'get_chat') else None
            sender = await event.get_sender() if hasattr(event, 'get_sender') else None
            logger.debug(f"Fetched chat: {chat}, sender: {sender}")
        except Exception as e:
            logger.error(f"Failed to fetch chat or sender: {e}")
            return None, None
        return chat, sender

    def _validate_message_content(self, event: events.NewMessage) -> bool:
        raise NotImplementedError("Subclasses should implement this method!")

    async def __call__(self, event: events.NewMessage, *args, **kwargs) -> bool:
        logger.debug(f"Filtering message {event}")
        if not self._validate_message_content(event):
            logger.debug("Message content validation failed.")
            return False

        chat, sender = await self._get_chat_and_sender(event)
        if not chat or not sender:
            logger.debug("Chat or sender validation failed.")
            return False

        if not self._check_sender_restrictions(sender):
            logger.debug("Sender restriction validation failed.")
            return False

        result = self._validate_source_type(chat)
        logger.debug(f"Final source type validation result: {result}")
        return result

    def __str__(self) -> str:
        return f"MediaFilter(source_type={self.source_type})"


class TextFilterNewMessage(MediaFilter):
    """Фильтр, проверяющий только текстовые сообщения в зависимости от указанного типа источника."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        result = bool(event and event.message and event.message.text and not event.message.media)
        logger.debug(f"Validated message content for text and non-media: {result}")
        return result


class AudioFilter(MediaFilter):
    ...


class DocumentFilter(MediaFilter):
    ...


class VideoFilter(MediaFilter):
    ...


@events.register(events.NewMessage(
    incoming=True,
    func=lambda e: e.message.text and not e.message.media
))
async def handle_text_messages(event):
    logger.info(f"Получено текстовое сообщение: {event.message.text}")


# Фильтр сообщений с видео
@events.register(events.NewMessage(
    incoming=True,
    func=lambda e: e.message.video is not None
))
async def handle_video_messages(event):
    logger.info("Получено видео сообщение")
    video = event.message.video
    logger.info(f"Длительность видео: {video.duration} секунд")


# Фильтр сообщений с документами
@events.register(events.NewMessage(
    incoming=True,
    func=lambda e: e.message.document is not None
))
async def handle_document_messages(event):
    logger.info("Получен документ")
    doc = event.message.document
    logger.info(f"Имя файла: {doc.attributes[0].file_name}")


# Фильтр голосовых сообщений
@events.register(events.NewMessage(
    incoming=True,
    func=lambda e: e.message.voice is not None
))
async def handle_voice_messages(event):
    logger.info("Получено голосовое сообщение")
    voice = event.message.voice
    logger.info(f"Длительность: {voice.duration} секунд")


# Фильтр по нескольким условиям (например, текст + фото)
@events.register(events.NewMessage(
    incoming=True,
    func=lambda e: e.message.photo is not None and e.message.text
))
async def handle_photo_with_caption(event):
    logger.info(f"Получено фото с подписью: {event.message.text}")
