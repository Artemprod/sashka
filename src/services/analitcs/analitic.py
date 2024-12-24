import asyncio
import uuid
from abc import ABC
from abc import abstractmethod
from io import BytesIO
from pathlib import Path
from typing import Optional
from typing import Union

from loguru import logger

from src.database.postgres.engine.session import DatabaseSessionManager
from src.services.analitcs.decorator.collector import AnalyticCollector
from src.services.analitcs.diolog import ResearchDialogs
from src.services.analitcs.exporters import CsvExporter
from src.services.analitcs.exporters import ExcelExporter
from src.services.analitcs.metrics import BasicMetricCalculator
from src.services.analitcs.metrics import MetricCalculator
from src.services.analitcs.models.analitic import AnalyticDataBufferDTO
from src.services.analitcs.models.analitic import AnalyticFileDTO


class Analytic(ABC):
    def __init__(self,
                 research_id: int,
                 session_manager,
                 metric_calculator):
        self.research_id = research_id
        self._session_manager = session_manager
        self.metric_calculator: MetricCalculator = metric_calculator(
            research_id=research_id, session_manager=session_manager
        )
        self._dialogs: Optional[ResearchDialogs] = None

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
                research_id=self.research_id,
                session_manager=self._session_manager
            )
            self._dialogs = await dialogs_object.get_dialogs()
        except Exception as e:
            logger.error(f"Ошибка загрузки диалогов: {e}")
            raise

    @abstractmethod
    async def provide_data(self, *args, **kwargs):
        """возвращает серию файлов: отдельные файлы для диалогов, отдельный файл для аналитики"""
        pass

    async def _process_dialogs(self, dialogs_objects, folder_path, exporter_cls, file_extension):
        dialogs = []
        metric_path = None

        for user_telegram_id, dialog in dialogs_objects.items():
            if not folder_path:
                dialog_buffer_data = await getattr(dialog, f"get_{file_extension}_buffer")()
                dialogs.append(dialog_buffer_data)
            else:
                dialog_path = str(Path(folder_path) / f"dialog_{user_telegram_id}.{file_extension}")
                metric_path = str(Path(folder_path) / f"metric_{uuid.uuid4()}.{file_extension}")
                dialog_file_data = await getattr(dialog, f"get_{file_extension}_file")(dialog_path)
                dialogs.append(dialog_file_data)

        metrics = await self.metric_calculator.analyze()

        if all(isinstance(dialog, BytesIO) for dialog in dialogs):
            return AnalyticDataBufferDTO(
                dialogs=dialogs,
                metric=exporter_cls.export_buffer([metrics]),
            )
        elif all(isinstance(dialog, str) for dialog in dialogs):
            return AnalyticFileDTO(
                dialogs=dialogs,
                metric=exporter_cls.export(data=[metrics], filepath=metric_path),
            )
        else:
            logger.info(f"Unknown format of objects in dialogs: {[type(dialog) for dialog in dialogs]}")
            raise ValueError(f"Unknown format of objects in dialogs: {[type(dialog) for dialog in dialogs]}")



class AnalyticCSV(Analytic):
    type = 'csv'
    """Возвращает серию файлов: отдельные файлы для диалогов, отдельный файл для аналитики в формате csv."""

    async def provide_data(self, folder_path: str = None) -> Union[AnalyticDataBufferDTO, AnalyticFileDTO]:
        """Возвращает список csv по диалогам и аналитик."""
        dialogs_objects = await self.dialogs
        return await self._process_dialogs(dialogs_objects.dialogs, folder_path, CsvExporter, 'csv')



class AnalyticExcel(Analytic):
    type = 'excel'
    """Возвращает серию файлов: отдельные файлы для диалогов, отдельный файл для аналитики в формате excel."""

    async def provide_data(self, folder_path: str = None) -> Union[AnalyticDataBufferDTO, AnalyticFileDTO]:
        """Возвращает список excel по диалогам и аналитик."""
        dialogs_objects = await self.dialogs
        return await self._process_dialogs(dialogs_objects.dialogs, folder_path, ExcelExporter, 'excel')

class AnalyticJsonDialogs(Analytic):
    type = 'json'

    async def provide_data(self, folder_path: str = None):
        """Возвращает список диалогов по иследованию."""
        dialogs_objects:ResearchDialogs = await self.dialogs
        result = await dialogs_objects.to_json()
        return result


