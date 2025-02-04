import asyncio
from datetime import datetime
from typing import List, Any, Tuple, Dict

from loguru import logger

from src.database.repository.storage import RepoStorage


class Context:
    """Класс формирующий контекст общения"""

    def __init__(self, research_id, telegram_client_id, assistant_id, user_telegram_id, chat_id):
        self.research_id = research_id
        self.user_telegram_id = user_telegram_id
        self.telegram_client_id = telegram_client_id
        self.assistant_id = assistant_id
        self.chat_id = chat_id

    async def load_from_repo(self, repo: "RepoStorage") -> List[Dict[str, str]]:
        try:
            user_messages, assistant_messages = await self._get_messages(repo)
            messages = self._combine_and_format_messages(user_messages, assistant_messages)
            sorted_messages = sorted(messages, key=lambda x: x[1])
            return [{"role": msg["role"], "content": msg["content"]} for msg, _ in sorted_messages]
        except Exception as e:
            logger.error(f"Error forming context for user {self.user_telegram_id}: {str(e)}")
            raise

    async def _get_messages(self, repo: "RepoStorage") -> Tuple[List[Any], List[Any]]:
        user_messages_future = repo.message_repo.user.get_context_messages(
            user_telegram_id=self.user_telegram_id,
            chat_id=self.chat_id,
            research_id=self.research_id,
            telegram_client_id=self.telegram_client_id,
            assistant_id=self.assistant_id,
        )

        assistant_messages_future = repo.message_repo.assistant.get_context_messages(
            user_telegram_id=self.user_telegram_id,
            chat_id=self.chat_id,
            research_id=self.research_id,
            telegram_client_id=self.telegram_client_id,
            assistant_id=self.assistant_id,
        )

        return await asyncio.gather(user_messages_future, assistant_messages_future)

    def _combine_and_format_messages(
        self, user_messages: List[Any], assistant_messages: List[Any]
    ) -> List[Tuple[Dict[str, str], datetime]]:
        formatted_messages = []
        formatted_messages.extend(self._format_messages(user_messages, "user"))
        formatted_messages.extend(self._format_messages(assistant_messages, "assistant"))
        return formatted_messages

    @staticmethod
    def _format_messages(messages: List[Any], role: str) -> List[Tuple[Dict[str, str], datetime]]:
        return [({"role": role, "content": msg.text}, msg.created_at) for msg in messages]


if __name__ == "__main__":
    a = Context()
