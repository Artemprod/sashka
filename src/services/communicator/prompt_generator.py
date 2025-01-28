from abc import ABC
from abc import abstractmethod
from typing import Optional

from aiocache import Cache
from aiocache import cached

from src.database.repository.storage import RepoStorage
from src.schemas.communicator.prompt import PromptDTO
from src.schemas.service.assistant import AssistantDTOGet
from src.schemas.service.prompt import PingPromptDTO


class BasePromptGenerator(ABC):
    # TODO Добавить кэширование промпта чтобы каждый раз не обращаться в бвзу за промптом к одному и тому же иследованию
    def __init__(self, repository: RepoStorage):
        self.repository = repository

    @abstractmethod
    async def generate_prompt(self, research_id, user_telegra_id, *args, **kwargs) -> PromptDTO:
        pass

    async def get_user_name(self, user_telegram_id: int) -> str:
        return await self.repository.user_in_research_repo.short.get_first_name_by_telegram_id(
            telegram_id=user_telegram_id
        )

    async def _get_assistant(self, research_id) -> Optional[AssistantDTOGet]:
        return await self.repository.assistant_repo.get_assistant_by_research(research_id=research_id)

    async def _get_stop_word_message_for_assistant(self) -> str:
        configuration = await self.repository.configuration_repo.get()
        return configuration.stop_word


# TODO набор параметров которые необходимо передать в промпт вынести в базу
class Prompter(BasePromptGenerator):
    async def generate_prompt(self, research_id, user_telegram_id, *args, **kwargs) -> PromptDTO:
        assistant = await self._get_assistant(research_id=research_id)

        if not assistant:
            raise ValueError("Assistant not found")

        user_prompt_part = assistant.first_message_prompt or ""
        user_prompt = f"{user_prompt_part} {assistant.user_prompt}".strip()

        placeholders = {}
        if "{name}" in assistant.system_prompt:
            placeholders["name"] = await self.get_user_name(user_telegram_id)
        if "{stop_word}" in assistant.system_prompt:
            placeholders["stop_word"] = await self._get_stop_word_message_for_assistant()

        if placeholders:
            assistant.system_prompt = assistant.system_prompt.format(**placeholders)

        return PromptDTO(user_prompt=user_prompt, system_prompt=assistant.system_prompt)




class CommonMessagePromptGenerator(BasePromptGenerator):
    async def generate_prompt(self, assistant_id, *args, **kwargs) -> PromptDTO:
        # TODO Вынесе ты блять уже этих ассистентов в отделный модуль заебал !
        assistant: AssistantDTOGet = await self.repository.assistant_repo.get_assistant(assistant_id=assistant_id)
        if not assistant:
            raise
        user_prompt_part = assistant.middle_part_prompt if assistant.middle_part_prompt else ""
        user_prompt = f"{user_prompt_part} {assistant.user_prompt} {args} {kwargs}"
        stop_word_message = await self._get_stop_word_message_for_assistant()
        return PromptDTO(user_prompt=user_prompt, system_prompt=f"{assistant.system_prompt} {stop_word_message}")


class PingPromptGenerator(BasePromptGenerator):
    async def generate_prompt(
        self,
        message_number: int,
    ) -> PromptDTO:
        try:
            prompt: PingPromptDTO = await self.repository.ping_prompt_repo.get_ping_prompt_by_order_number(
                ping_order_number=message_number
            )
            stop_word_message = await self._get_stop_word_message_for_assistant()
            return PromptDTO(user_prompt=prompt.prompt, system_prompt=f"{prompt.system_prompt} {stop_word_message}")
        except Exception as e:
            raise e


class PromptGenerator:
    def __init__(self, repository: RepoStorage):
        self.prompter = Prompter(repository=repository)
        self.common_prompt_generator = CommonMessagePromptGenerator(repository=repository)

    async def generate_first_message_prompt(self, research_id, telegram_user_id):
        return await self.prompter.generate_prompt(research_id=research_id, user_telegram_id=telegram_user_id)

    async def generate_research_prompt(self, research_id, telegram_user_id) -> PromptDTO:
        return await self.prompter.generate_prompt(research_id, telegram_user_id)


class ExtendedPingPromptGenerator(PromptGenerator):
    def __init__(self, repository: RepoStorage):
        PromptGenerator.__init__(self, repository=repository)
        self.ping_prompt_generator = PingPromptGenerator(repository=repository)

    async def generate_ping_prompt(self, message_number: int) -> PromptDTO:
        return await self.ping_prompt_generator.generate_prompt(message_number=message_number)
