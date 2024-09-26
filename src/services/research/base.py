from abc import ABC, abstractmethod


class BaseResearchManager(ABC):

    @abstractmethod
    async def create_research(self, *args, **kwargs):
        pass

