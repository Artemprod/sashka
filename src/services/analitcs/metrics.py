import asyncio
from abc import ABC
from abc import abstractmethod
from typing import Optional

from loguru import logger

from src.database.postgres.engine.session import DatabaseSessionManager
from src.services.analitcs.diolog import ResearchDialogs
from src.services.analitcs.diolog import UserDialog
from src.services.analitcs.models.metrics import DialogMetrics


class MetricCalculator(ABC):
    """Абстрактный класс для анализа диалогов."""

    @abstractmethod
    async def analyze(self) -> DialogMetrics:
        pass


class BasicMetricCalculator(MetricCalculator):
    def __init__(
        self, research_status: str, research_id: int, session_manager, dialogs: Optional[ResearchDialogs] = None
    ):
        self.research_id = research_id
        self._session_manager = session_manager
        self._research_status: str = research_status
        self._dialogs: Optional[ResearchDialogs] = dialogs

    @property
    async def dialogs(self) -> ResearchDialogs:
        """Ленивая загрузка диалогов."""
        if self._dialogs is None:
            await self._load_dialogs()
        return self._dialogs

    async def _load_dialogs(self) -> None:
        """Загрузка диалогов для исследования."""
        try:
            dialogs_object = ResearchDialogs(
                research_status=self._research_status,
                research_id=self.research_id,
                session_manager=self._session_manager,
            )
            self._dialogs = await dialogs_object.get_dialogs()
        except Exception as e:
            logger.error(f"Ошибка загрузки диалогов: {e}")
            raise

    async def _count_first_message_responses(self) -> int:
        """Подсчет количества диалогов с ответом пользователя вторым сообщением."""
        dialogs = await self.dialogs
        counter = 0

        for user_id, dialog in dialogs.dialogs.items():
            if not isinstance(dialog, UserDialog):
                logger.error(f"Неверный формат данных диалога для user_id {user_id}")
                continue

            try:
                if dialog.dialog.iloc[1]["is_user"]:
                    counter += 1
            except IndexError:
                logger.debug(f"Диалог слишком короткий для user_id {user_id}")
                continue

        return counter

    async def analyze(self) -> DialogMetrics:
        """Анализ диалогов и подсчет метрик."""
        dialogs = await self.dialogs
        total = len(dialogs.dialogs)

        if total == 0:
            logger.warning("Нет доступных диалогов для расчета конверсии")
            return DialogMetrics(total_dialogs=0, answered_first=0, conversion_rate=0.0)

        answered = await self._count_first_message_responses()
        conversion = round((answered / total) * 100, 2)

        return DialogMetrics(total_dialogs=total, answered_first=answered, conversion_rate=conversion)

    # Методы для обратной совместимости
    async def total_interviewed(self) -> int:
        """Получение общего количества диалогов."""
        metrics = await self.analyze()
        return metrics.total_dialogs

    async def count_first_message_answer(self) -> int:
        """Подсчет ответов на первое сообщение."""
        metrics = await self.analyze()
        return metrics.answered_first

    async def first_answer_conversion(self) -> float:
        """Расчет конверсии ответов на первое сообщение."""
        metrics = await self.analyze()
        return metrics.conversion_rate

    async def completed_dialog_conversion(self): ...
