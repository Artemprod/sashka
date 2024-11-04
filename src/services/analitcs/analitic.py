from abc import abstractmethod, ABC


class Analytic(ABC):

    def __init__(self, research_id: int, session_manager):
        self.research_id = research_id
        self._session_manager = session_manager

    @abstractmethod
    async def provide_data(self):
        """
        возвращет серию файлов отдельные файлы для диалогов отдельный фал для аналитики
        :return:
        """
        ...


class AnalyticCSV(Analytic):
    """

    возвращет серию файлов отдельные файлы для диалогов отдельный фал для аналитики в формате csv
    """
    async def provide_data(self):
        pass

    ...

class AnalyticExcel(Analytic):
    async def provide_data(self):
        pass

    ...
