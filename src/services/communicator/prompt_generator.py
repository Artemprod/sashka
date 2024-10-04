from abc import ABC, abstractmethod
from functools import lru_cache, cache

from typing import Union, List, Optional

from src.schemas.communicator.prompt import PromptDTO

from src.schemas.service.assistant import AssistantDTOGet

from src_v0.database.repository.storage import RepoStorage

from abc import ABC


class BasePromptGenerator(ABC):
    # TODO Добавить кэширование промпта чтобы каждый раз не обращаться в бвзу за промптом к одному и тому же иследованию
    def __init__(self, repository: RepoStorage):
        self.repository = repository

    @abstractmethod
    async def generate_prompt(self, research_id, *args, **kwargs) -> PromptDTO:
        pass

    @cache
    async def _get_assistant(self, research_id) -> Optional[AssistantDTOGet]:
        return await self.repository.assistant_repo.get_assistant_by_research(research_id=research_id)


# TODO вообще можно сократить количесвто кода и просто отправлять ассистента это я че то тут заморочился
class FirstMessagePromptGenerator(BasePromptGenerator):
    @cache
    async def generate_prompt(self, research_id, *args, **kwargs) -> PromptDTO:
        assistant = await self._get_assistant(research_id=research_id)
        if not assistant:
            raise
        user_prompt_part = assistant.first_message_prompt if assistant.first_message_prompt else ""
        user_prompt = f"{user_prompt_part} {assistant.user_prompt} {args} {kwargs}"
        return PromptDTO(
            user_prompt=user_prompt,
            system_prompt=assistant.system_prompt
        )


class ResearchMessagePromptGenerator(BasePromptGenerator):

    @cache
    async def generate_prompt(self, research_id, *args, **kwargs) -> PromptDTO:
        assistant = await self._get_assistant(research_id=research_id)
        if not assistant:
            raise
        user_prompt_part = assistant.middle_part_prompt if assistant.middle_part_prompt else ""
        user_prompt = f"{user_prompt_part} {assistant.user_prompt} {args} {kwargs}"
        return PromptDTO(
            user_prompt=user_prompt,
            system_prompt=assistant.system_prompt
        )


class CommonMessagePromptGenerator(BasePromptGenerator):

    @cache
    async def generate_prompt(self, assistant_id, *args, **kwargs) -> PromptDTO:
        # TODO Вынесе ты блять уже этих ассистентов в отделный модуль заебал !
        assistant: AssistantDTOGet = await self.repository.assistant_repo.get_assistant(assistant_id=assistant_id)
        if not assistant:
            raise
        user_prompt_part = assistant.middle_part_prompt if assistant.middle_part_prompt else ""
        user_prompt = f"{user_prompt_part} {assistant.user_prompt} {args} {kwargs}"
        return PromptDTO(
            user_prompt=user_prompt,
            system_prompt=assistant.system_prompt
        )


class PromptGenerator:

    def __init__(self, repository:RepoStorage):

        self.first_message_generator = FirstMessagePromptGenerator(repository=repository)
        self.research_prompt_generator = ResearchMessagePromptGenerator(repository=repository)
        self.common_prompt_generator = CommonMessagePromptGenerator(repository=repository)

    @cache
    async def generate_first_message_prompt(self, research_id):
        return await self.first_message_generator.generate_prompt(research_id=research_id)

    @cache
    async def generate_research_prompt(self, research_id) -> PromptDTO:
        return await self.research_prompt_generator.generate_prompt(research_id)

    @cache
    async def generate_common_prompt(self,assistant_id:int) -> PromptDTO:
        return await self.common_prompt_generator.generate_prompt(assistant_id=assistant_id)