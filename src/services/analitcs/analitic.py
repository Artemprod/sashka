import asyncio
from abc import abstractmethod, ABC
from io import BytesIO
from typing import Optional, Union

from loguru import logger

from src.database.postgres.engine.session import DatabaseSessionManager
from src.services.analitcs.decorator.collector import AnalyticCollector
from src.services.analitcs.diolog import ResearchDialogs
from src.services.analitcs.metrics import MetricCalculator, BasicMetricCalculator
from src.services.analitcs.models.analitic import AnalyticDataBufferDTO, AnalyticFileDTO


class Analytic(ABC):
    def __init__(self,
                 research_id: int,
                 session_manager,
                 metric_calculator):
        self.research_id = research_id
        self._session_manager = session_manager
        self.metric_calculator: MetricCalculator = metric_calculator(
            research_id=research_id,
            session_manager=session_manager
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
        """
        возвращает серию файлов:
        отдельные файлы для диалогов,
        отдельный файл для аналитики
        """
        pass


@AnalyticCollector
class AnalyticCSV(Analytic):
    type = 'csv'
    """
    Возвращает серию файлов:
    отдельные файлы для диалогов,
    отдельный файл для аналитики в формате csv
    """

    async def provide_data(self, path: str = None) -> Union[AnalyticDataBufferDTO, AnalyticFileDTO]:
        """ Возвращает список csv по диалогам и аналитик """
        dialogs_objects = await self.dialogs
        dialogs = []

        for user_telegram_id, dialog in dialogs_objects.dialogs.items():
            if not path:
                dialog_buffer_data = await dialog.get_csv_buffer()
                dialogs.append(dialog_buffer_data)
            else:
                dialog_file_data = await dialog.get_csv_file(path)
                dialogs.append(dialog_file_data)

        metrics = await self.metric_calculator.analyze()

        if all(isinstance(dialog, BytesIO) for dialog in dialogs):
            return AnalyticDataBufferDTO(
                dialogs=dialogs,
                metric=metrics,
            )
        elif all(isinstance(dialog, str) for dialog in dialogs):
            return AnalyticFileDTO(
                dialogs=dialogs,
                metric=metrics,
            )
        else:
            logger.info(f"Unknown format of objects in dialogs: {(type(dialog) for dialog in dialogs)}")
            raise ValueError(f"Unknown format of objects in dialogs: {(type(dialog) for dialog in dialogs)}")


@AnalyticCollector
class AnalyticExcel(Analytic):
    type = 'excel'
    """
    Возвращает серию файлов:
    отдельные файлы для диалогов,
    отдельный файл для аналитики в формате excel
    """

    async def provide_data(self, path: str = None) -> Union[AnalyticDataBufferDTO, AnalyticFileDTO]:
        """ Возвращает список excel по диалогам и аналитик """
        dialogs_objects = await self.dialogs
        dialogs = []

        for user_telegram_id, dialog in dialogs_objects.dialogs.items():
            if not path:
                dialog_buffer_data = await dialog.get_excel_buffer()
                dialogs.append(dialog_buffer_data)
            else:
                dialog_file_data = await dialog.get_excel_file(path)
                dialogs.append(dialog_file_data)

        metrics = await self.metric_calculator.analyze()

        if all(isinstance(dialog, BytesIO) for dialog in dialogs):
            return AnalyticDataBufferDTO(
                dialogs=dialogs,
                metric=metrics,
            )
        elif all(isinstance(dialog, str) for dialog in dialogs):
            return AnalyticFileDTO(
                dialogs=dialogs,
                metric=metrics,
            )
        else:
            logger.info(f"Unknown format of objects in dialogs: {(type(dialog) for dialog in dialogs)}")
            raise ValueError(f"Unknown format of objects in dialogs: {(type(dialog) for dialog in dialogs)}")

if __name__ == "__main__":
    async def main():
        session = DatabaseSessionManager(
            database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client')
        csv_class:AnalyticCSV= AnalyticCollector.instruments['csv'](research_id=80,
                                                                    session_manager=session,
                                                                    metric_calculator=BasicMetricCalculator)
        excel_class = AnalyticCollector.instruments['excel'](research_id=80,
                                                                    session_manager=session,
                                                                    metric_calculator=BasicMetricCalculator)
        print(csv_class)  # Должно напечатать класс AnalyticCSV
        print(excel_class)  # Должно напечатать класс AnalyticExcel
        r = await excel_class.provide_data(path=r'D:\projects\AIPO_V2\CUSTDEVER\src\services\analitcs\test.xlsx')
        print(r)


    asyncio.run(main())