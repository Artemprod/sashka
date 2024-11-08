from enum import Enum
from typing import Optional, List, Union, Tuple

from environs import Env
from loguru import logger
from telethon import events
from telethon.tl.types import PeerUser, PeerChat, PeerChannel, User, Chat, Channel, DocumentAttributeAudio

from configs.telegram_account import telegram_account_allowance_policy
from src.distributor.telegram_client.telethoncl.filters.model import SourceType
from telethon.tl.types import (
    MessageMediaDocument,
    MessageMediaPhoto,
    DocumentAttributeAudio,
    DocumentAttributeVideo,
    DocumentAttributeSticker,
    DocumentAttributeAnimated,
    MessageMediaContact,
    MessageMediaGeo,
    MessageMediaVenue,
    MessageMediaPoll
)


class Filter:
    """Базовый фильтр с логикой обработки системных и ограниченных пользователей."""

    SourceType = SourceType

    TELEGRAM_SYSTEM_ACCOUNTS: List[Union[str, int]] = [
        "@PremiumBot", "@Prremiummm_bot", "@Telegram", "@PassportBot", "@GDPRbot",
        "@BotSupport", "@MTProxybot", "@DiscussBot", "@WebAppsBot",
        "@DurgerKingBot", "@BotFather", "@SpamBot", "@GameBot",
        "777000", "333000", "42777",
        "@QuizBot", "@TranslateBot", "@StoreBot", "@LotteryBot",
        "@GroupButler_bot", "@Stickers"
    ]

    RESTRICTED_USERS: Optional[List[Union[str, int]]] = []

    def __init__(self):
        self.settings = telegram_account_allowance_policy
        logger.debug("Initializing Filter...")
        restricted_users = self._load_restricted_users()

        if not Filter.RESTRICTED_USERS:
            Filter.RESTRICTED_USERS = restricted_users
            logger.info("Initialized restricted users from environment.")
        else:
            new_users = set(restricted_users) - set(Filter.RESTRICTED_USERS)
            if new_users:
                Filter.RESTRICTED_USERS.extend(new_users)
                logger.info("Updated restricted users with new entries.")

        services = self._load_restricted_services()
        if services:
            new_services = set(services) - set(Filter.TELEGRAM_SYSTEM_ACCOUNTS)
            if new_services:
                Filter.TELEGRAM_SYSTEM_ACCOUNTS.extend(new_services)
                logger.info("Updated services with new entries.")

    def _load_restricted_users(self) -> List[Union[str, int]]:
        try:
            logger.debug("Loading restricted users from configs...")
            users = self.settings.not_allowed_users_id + self.settings.not_allowed_users_usernames
            return users
        except Exception as e:
            logger.debug("Loading restricted users from .env...")
            env = Env()
            env.read_env('.env')
            try:
                users = list(env("NOT_ALLOWED_USERS_ID", "").split(","))
                logger.debug(f"Loaded restricted users: {users}")
                return users
            except Exception as e:
                logger.error("Failed to load restricted users from .env: {}", exc_info=e)
                raise

    def _load_restricted_services(self) -> List[Union[str, int]]:
        try:
            logger.debug("Loading restricted services from configs...")
            new_services = self.settings.not_allowed_services
            return new_services
        except Exception as e:
            logger.debug("Loading restricted services from .env...")
            env = Env()
            env.read_env('.env')
            try:
                new_services = list(env("NOT_ALLOWED_SERVICES", "").split(","))
                logger.debug(f"Loaded restricted services: {new_services}")
                return new_services
            except Exception as e:
                logger.error("Failed to load restricted services from .env: {}", exc_info=e)
                raise

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

    def __init__(self, source_type: Union[str, Filter.SourceType] = Filter.SourceType.ANY, ):
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
        sender_username = sender.username
        sender_id = str(sender.id)

        result = not (
                self.is_system_account(sender_username) or
                self.is_restricted(sender_username)
        ) and not (
                self.is_system_account(sender_id) or
                self.is_restricted(sender_id)
        )
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

        # Сравнение ID отправителя с моим ID
        me = await event.client.get_me()
        if sender.id == me.id:
            logger.debug(f"Message is from self (id: {me.id}), blocking.")
            return False

        if not self._check_sender_restrictions(sender):
            logger.debug("Sender restriction validation failed.")
            return False

        result = self._validate_source_type(chat)
        logger.debug(f"Final source type validation result: {result}")
        return result

    def __str__(self) -> str:
        return f"MediaFilter(source_type={self.source_type})"


class TextFilter(MediaFilter):
    """Фильтр, проверяющий только текстовые сообщения."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        result = bool(event and event.message and event.message.text and not event.message.media)
        logger.debug(f"Validated text message content: {result}")
        return result


class VoiceFilter(MediaFilter):
    """Фильтр, проверяющий наличие голосового сообщения."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        if not (event.message and isinstance(event.message.media, MessageMediaDocument)):
            return False

        # Проверяем атрибуты документа на наличие голосового сообщения
        doc = event.message.media.document
        is_voice = any(
            isinstance(attr, DocumentAttributeAudio) and attr.voice
            for attr in doc.attributes
        )
        logger.debug(f"Validated voice message content: {is_voice}")
        return is_voice


class AudioFilter(MediaFilter):
    """Фильтр, проверяющий наличие аудиофайла."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        if not (event.message and isinstance(event.message.media, MessageMediaDocument)):
            return False

        doc = event.message.media.document
        is_audio = any(
            isinstance(attr, DocumentAttributeAudio) and not attr.voice
            for attr in doc.attributes
        )
        logger.debug(f"Validated audio message content: {is_audio}")
        return is_audio


class VideoFilter(MediaFilter):
    """Фильтр, проверяющий наличие видеофайла."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        if not (event.message and isinstance(event.message.media, MessageMediaDocument)):
            return False

        doc = event.message.media.document
        is_gif = any(
            isinstance(attr, DocumentAttributeAnimated)
            for attr in doc.attributes
        )
        is_video = any(
            isinstance(attr, DocumentAttributeVideo) and not attr.round_message
            for attr in doc.attributes
        ) and not is_gif

        logger.debug(f"Validated video message content: {is_video}")
        return is_video


class PhotoFilter(MediaFilter):
    """Фильтр, проверяющий наличие фотографии."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        result = bool(event.message and isinstance(event.message.media, MessageMediaPhoto))
        logger.debug(f"Validated photo message content: {result}")
        return result


class StickerFilter(MediaFilter):
    """Фильтр, проверяющий наличие стикера."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        if not (event.message and isinstance(event.message.media, MessageMediaDocument)):
            return False

        doc = event.message.media.document
        is_sticker = any(
            isinstance(attr, DocumentAttributeSticker)
            for attr in doc.attributes
        )
        logger.debug(f"Validated sticker message content: {is_sticker}")
        return is_sticker


class GifFilter(MediaFilter):
    """Фильтр, проверяющий наличие анимации (GIF)."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        if not (event.message and isinstance(event.message.media, MessageMediaDocument)):
            return False

        doc = event.message.media.document

        is_gif = any(
            isinstance(attr, DocumentAttributeAnimated)
            for attr in doc.attributes
        )

        logger.debug(f"Validated animated gif content: {is_gif}")
        return is_gif


class ContactFilter(MediaFilter):
    """Фильтр, проверяющий наличие контактной информации."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        result = bool(event.message and isinstance(event.message.media, MessageMediaContact))
        logger.debug(f"Validated contact message content: {result}")
        return result


class LocationFilter(MediaFilter):
    """Фильтр, проверяющий наличие информации о местоположении."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        has_geo = isinstance(event.message.media, MessageMediaGeo)
        has_venue = isinstance(event.message.media, MessageMediaVenue)
        result = bool(event.message and (has_geo or has_venue))
        logger.debug(f"Validated location content: {result}")
        return result


class PollFilter(MediaFilter):
    """Фильтр, проверяющий наличие опроса."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        result = bool(event.message and isinstance(event.message.media, MessageMediaPoll))
        logger.debug(f"Validated poll content: {result}")
        return result


class ForwardFilter(MediaFilter):
    """Фильтр, проверяющий, является ли сообщение пересланным."""

    def _validate_message_content(self, event: events.NewMessage.Event) -> bool:
        result = bool(event.message and event.message.fwd_from)
        logger.debug(f"Validated forwarded message: {result}")
        return result
