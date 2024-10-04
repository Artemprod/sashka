from src.schemas.communicator.checker import CheckerDTO


class Checker:

    def __init__(self, repository):
        self.repository = repository

    async def _is_user_in_database(self,user_telegram_id:int)->bool:
        ...

    async def _is_user_in_research(self,user_telegram_id:int)->bool:
        ...

    async def _get_user_research_id(self,user_telegram_id:int)->int:
        ...

    async def check_user(self, user_telegram_id:int) -> CheckerDTO:
        return CheckerDTO()
