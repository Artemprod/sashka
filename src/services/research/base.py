from abc import ABC
from abc import abstractmethod


class BaseResearchManager(ABC):
    @abstractmethod
    async def create_research(self, *args, **kwargs):
        pass
