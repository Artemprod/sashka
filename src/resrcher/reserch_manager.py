import asyncio
import datetime
from datetime import date

from faststream.nats import NatsBroker

from datasourse_for_test.resercch_imirtation import UserResearch

from src.database.database_t import comon_database as reserch_database
from src.resrcher.user_cimmunication import send_first_message
from src.resrcher.user_manager import ping_users, set_all_user_status_done


def create_research(info) -> UserResearch:
    """

    1. Получить данные об иследовании
     - Собрать информацию о пользователях ( менеджер пользователей )

    2. Получить статус WAIT для иследования
    3. Получить статус WAIT для пользователя

    4. Привязать клиента
        - Выбрать подходящего клиента ( менеджер клиента )
    5. Привязать ассистента
        - выбрать подходящего асситента ( менеджер асиситентов

    6. Сохоанить данные в базу
    7. Поставить статтус ожидания для иследования
    8. Положить пользователей в базу данных
    9. Поставить им статус ожидания
    10. Привязать пользователй к иследованию

    :param info:
    :return:
    """
    research = UserResearch(
        owner="Artem",
        client="",
        research_id="res004",
        title="Анализ времени активности пользователей",
        theme="Временные паттерны активности",
        status=0,
        start_date=date(2024, 9, 1),
        end_date=date(2024, 9, 30),
        user_ids=[401, 402, 403]
    )
    reserch_database.save(research.research_id, research)
    return research


async def is_research_time_over(research_id, event):
    research: UserResearch = reserch_database.get(name=research_id)

    # TODO можно сразу вычислять в базе и выдвать дни
    days = (research.end_date - research.start_date).days
    while days > 0:
        if research.status != 1:
            print(f"Звершил иследование по изменению статуса {research.theme}")
            break

        print('проверяю оставшееся время это вот столько ', days)
        print('статус иследования ', research.status)
        difference = research.end_date - date.today()
        days = difference.days
        await asyncio.sleep(1)
    else:
        # TODO Всех пользователей в статус done
        event.set()
        print(f"Звершил иследование по истечению времени {research.theme}")


async def is_users_over(research_id, event):
    research: UserResearch = reserch_database.get(name=research_id)

    if not len(reserch_database.data['user_in_progress']) != 0:
        print('Нету пользователей в иследовании')
        #TODO Подумать что возвращает
        return None
    else:
        users = len(reserch_database.data['user_in_progress'])
        while users > 0:
            if research.status != 1:
                break
            print('проверяю пользователей в прогрессе их вот столько', reserch_database.data['user_in_progress'])
            users = len(reserch_database.data['user_in_progress'])
            await asyncio.sleep(1)
        else:
            # TODO Всех пользователей в статус done
            event.set()
            print(f"Звершил иследование закончилоись пользоавтели {research.theme}")



async def start_research(research_id):
    """
    Задача начать иследование разослав сообщения пользоватеям
    :param research_id:
    :param client_id:
    :return:
    """

    research: UserResearch = reserch_database.get(name=research_id)
    research.status = 1

    # расссылка пиветсвенного сообщения и все
    await send_first_message(user_ids=reserch_database.data['user_in_progress'])


async def stop_research(research_id, event):
    """Функция отсанавливаетс иследование перводя его статус в необходимый если выполняется какое то из условий
    статусы
    2 - готово
    уведомить что закончено
    """
    """Какая то логика которая долджна выполнятся по зварешению иследования """
    print('Жду сигнала к завершению ...')
    await event.wait()
    research: UserResearch = reserch_database.get(name=research_id)
    research.status = 2
    # TODO Всех пользователей в статус done
    if research.status == 2 and await set_all_user_status_done(research_id=research):
        print("иследование завершено")


def abort_research(research_id):
    research: UserResearch = reserch_database.get(name=research_id)
    research.status = 4


def get_research_info(research_id):
    research: UserResearch = reserch_database.get(name=research_id)
    print(research)


async def del_users_in_progres():
    while len(reserch_database.data['user_in_progress']) != 0:
        user = reserch_database.data['user_in_progress'].pop()
        print(reserch_database.data['user_in_progress'])
        print(f"удалил пользователя  {user}")
        await asyncio.sleep(6)


async def main():
    event = asyncio.Event()
    research = create_research('eee')
    await start_research(research_id=research.research_id)
    # запустить отслеживание сигналов завершения
    await asyncio.gather(del_users_in_progres(),
                         ping_users(),
                         is_research_time_over(research.research_id, event),
                         is_users_over(research.research_id, event),stop_research(research.research_id,event))



if __name__ == '__main__':
    asyncio.run(main())
