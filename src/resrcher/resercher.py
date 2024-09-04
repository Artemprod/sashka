import asyncio
from datetime import date
from typing import Any, List

from datasourse_for_test.resercch_imirtation import UserResearch
from src.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum
from src.database.postgres.models.research import Research
from src.database.postgres.models.user import User
from src.database.repository.storage import RepoStorage
from src.resrcher.user_cimmunication import Communicator
from src.resrcher.user_manager import UserManager
from src.database.database_t import comon_database as reserch_database
from src.schemas.research import ResearchDTO, ResearchOwnerDTO
from src.schemas.user import UserDTO


class BaseResearcher:
    ...
#TODO Переделать входящие данные это должен быть DTO Research

class TelegramResearcher(BaseResearcher):
    def __init__(self, research: UserResearch, repository: RepoStorage):
        self.database_repository = repository
        self.research = research
        self.user_manager = UserManager()
        self.communicator = Communicator()
        self.settings = {
            "delay_is_research_time_over": 60,
            "delay_is_users_over": 10
        }

    async def create_research(self) :
        """Создает исследование в базе данных и назначает необходимые данные"""

        # Получить статусы
        user_status = await self._get_user_status(UserStatusEnum.WAIT)
        research_status = await self._get_research_status(ResearchStatusEnum.WAIT)
        assistant = await self._get_assistant(self.research.assistant_id)
        owner = await self._get_or_create_owner(self.research.owner.service_owner_id)
        telegram_client = await self._get_telegram_client()

        # Создать и сохранить исследование
        research_dto = self._create_research_dto(owner, research_status, assistant, telegram_client)
        db_research = await self._save_new_research(research_dto)

        # Собрать информацию о пользователях и добавить их в исследование
        users_dto = await self._collect_users_information(self.research.user_ids)
        db_users = await self._add_users_to_research(users_dto, user_status)

        # Связать пользователей с исследованием
        await self._bind_users_to_research(db_users, db_research.research_id)
        #TODO Тут вернуть DTO класс с иследованием полным
        saved_research = await self._get_saved_research(db_research.research_id)
        return saved_research


    async def _get_user_status(self, status_name: UserStatusEnum) -> Any:
        return await self.database_repository.status_repo.user_status.get_status(status_name=status_name)

    async def _get_research_status(self, status_name: ResearchStatusEnum) -> Any:
        return await self.database_repository.status_repo.research_status.get_status(status_name=status_name)

    async def _get_assistant(self, assistant_id: int) -> Any:
        return await self.database_repository.assistant_repo.get_assistant(assistant_id=assistant_id)

    async def _get_or_create_owner(self, service_owner_id: int) -> Any:
        owner = await self.database_repository.owner_repo().short.get_owner_by_service_id(service_id=service_owner_id)
        if not owner:
            owner_dto = ResearchOwnerDTO(**self.research.owner.to_dict())
            owner = await self.database_repository.owner_repo().short.add_owner(values=owner_dto.dict())
        return owner

    # TODO выдвать клиента как то по другому например по стасту активен не активен пока для теста так
    async def _get_telegram_client(self) -> Any:
        return await self.database_repository.client_repo.get_client_by_id(client_id=1)

    def _create_research_dto(self, owner: Any, research_status: Any, assistant: Any, telegram_client: Any) -> ResearchDTO:
        return ResearchDTO(
            owner_id=owner.owner_id,
            research_status_id=research_status.status_id,
            # assistant_id=assistant.assistant_id,
            telegram_client_id=telegram_client.telegram_client_id,
            **self.research.to_dict()
        )

    async def _save_new_research(self, research_dto: ResearchDTO) -> Any:
        return await self.database_repository.research_repo.short.save_new_research(values=research_dto.dict())

    # TODO Не забывай что тут возвращаются объекты модели данных а не DTO допиши конвертацию
    async def _get_saved_research(self, research_id: int) -> Any:
        return await self.database_repository.research_repo.full.get_research_by_id(research_id=research_id)

    async def _collect_users_information(self, user_telegram_ids: List[int]) -> List[UserDTO]:
        return await self.user_manager.collect_users_information(user_telegram_ids=user_telegram_ids)

    # TODO Не забывай что тут возвращаются объекты модели данных а не DTO допиши конвертацию
    async def _add_users_to_research(self, users_dto: List[UserDTO], status: Any) -> List[Any]:
        return await self.database_repository.user_in_research_repo.short.add_many_users(
            [{"status_id": status.status_id, **user.dict()} for user in users_dto]
        )

    async def _bind_users_to_research(self, db_users: List[Any], research_id: int) -> None:
        for db_user in db_users:
            await self.database_repository.user_in_research_repo.short.bind_research(user_id=db_user.user_id, research_id=research_id)




    async def is_research_time_over(self, event):

        days = (self.research.end_date - self.research.start_date).days
        while days > 0:
            if self.research.status != 1:
                print(f"Звершил иследование по изменению статуса {self.research.theme}")
                break

            print('проверяю оставшееся время это вот столько ', days)
            print('статус иследования ', self.research.status)
            difference = self.research.end_date - date.today()
            days = difference.days
            await asyncio.sleep(self.settings.get('delay_is_research_time_over', 60))
        else:
            # TODO Всех пользователей в статус done
            event.set()
            print(f"Звершил иследование по истечению времени {self.research.theme}")

    async def is_users_over(self, event):

        if not len(reserch_database.data['user_in_progress']) != 0:
            print('Нету пользователей в иследовании')
            # TODO Подумать что возвращает
            return None
        else:
            users = len(reserch_database.data['user_in_progress'])
            while users > 0:
                if self.research.status != 1:
                    break
                print('проверяю пользователей в прогрессе их вот столько', reserch_database.data['user_in_progress'])
                users = len(reserch_database.data['user_in_progress'])
                await asyncio.sleep(self.settings.get('delay_is_users_over', 10))
            else:
                # TODO Всех пользователей в статус done
                event.set()
                print(f"Звершил иследование закончилоись пользоавтели {self.research.theme}")

    async def start_research(self):
        """
        Задача начать иследование разослав сообщения пользоватеям
        :param research_id:
        :param client_id:
        :return:
        """
        # поставить статус иследования 1 (в работе)
        # первести всех пользователей в стус в работе
        # отправить приветсвенное сообщение
        self.research.status = 1
        # расссылка пиветсвенного сообщения и все
        await self.communicator.send_first_message(user_ids=reserch_database.data['user_in_progress'])

    async def stop_research(self, event):
        """Функция отсанавливаетс иследование перводя его статус в необходимый если выполняется какое то из условий
        статусы
        2 - готово
        уведомить что закончено
        """
        """Какая то логика которая долджна выполнятся по зварешению иследования """
        print('Жду сигнала к завершению ...')
        await event.wait()
        self.research.status = 2
        # TODO Всех пользователей в статус done
        # TODO Сохранить все данные в базу данных
        if self.research.status == 2 and await self.user_manager.set_all_user_status_done(
                research_id=self.research.research_id):
            print("иследование завершено")

    async def run_research(self):
        event = asyncio.Event()
        await self.create_research()
        await self.start_research()

        # запустить отслеживание сигналов завершения
        ping_task = self.user_manager.ping_users()
        is_research_time_over_task = self.is_research_time_over(event)
        is_users_over_task = self.is_users_over(event)
        stop_task = self.stop_research(event)
        return await asyncio.gather(ping_task, is_research_time_over_task, is_users_over_task, stop_task)

    def abort_research(self, ):
        self.research.status = 4

    def pause_research(self):
        self.research.status = 5

    def get_research_info(self, ):
        print(self.research)
