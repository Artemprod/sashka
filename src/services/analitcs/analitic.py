from abc import abstractmethod, ABC
from typing import Optional, Union

from loguru import logger

from src.services.analitcs.decorator.collector import AnalyticCollector
from src.services.analitcs.diolog import ResearchDialogs
from src.services.analitcs.metrics import MetricCalculator
from src.services.analitcs.models.analitic import AnalyticFileBufferDTO, AnalyticDataBufferDTO


class Analytic(ABC):

    def __init__(self,
                 research_id: int,
                 session_manager,
                 metric_calculator):
        self.research_id = research_id
        self._session_manager = session_manager
        self.metric_calculator:MetricCalculator = metric_calculator(research_id=research_id,
                                                                    session_manager=session_manager)
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
        возвращет серию файлов отдельные файлы для диалогов отдельный фал для аналитики
        :return:
        """

        pass



@AnalyticCollector
class AnalyticCSV(Analytic):
    type = 'csv'
    """

    возвращет серию файлов отдельные файлы для диалогов отдельный фал для аналитики в формате csv
    """

    async def provide_data(self, path:str=None)->Union[AnalyticDataBufferDTO,AnalyticFileBufferDTO]:
        """
        Возвращает спсок csv по дмлогам и аналитик
        :return:
        """
        dialogs_objects = await self.dialogs
        dialogs = []
        for user_telegram_id, dialog in dialogs_objects.dialogs.items():
            if not path:
                dialogs.append(dialog.get_csv_buffer())
            else:
                dialogs.append(dialog.get_csv_file(path))
        metrics =



@AnalyticCollector
class AnalyticExcel(Analytic):
    type = 'excel'

    async def provide_data(self):
        pass

    ...
