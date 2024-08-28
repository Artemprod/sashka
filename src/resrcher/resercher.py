import asyncio
from datetime import date

from datasourse_for_test.resercch_imirtation import UserResearch
from src.resrcher.user_cimmunication import Communicator
from src.resrcher.user_manager import UserManager
from src.database.database_t import comon_database as reserch_database


class Researcher:
    def __init__(self, research: UserResearch):
        self.database = reserch_database
        self.research = research
        self.user_manager = UserManager()
        self.communicator = Communicator()

    async def create_research(self) -> UserResearch:
        # Поставить статус wait
        #сохранить иследование в базу данных
        # добавить пользователей в базу данных присвоить статсу wait

        self.database.reserch_database.save(self.research.research_id, self.research)
        return self.research

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
            await asyncio.sleep(1)
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
                await asyncio.sleep(1)
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
        if self.research.status == 2 and await self.user_manager.set_all_user_status_done(research_id=self.research.research_id):
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

    def get_research_info(self, ):
        print(self.research)
