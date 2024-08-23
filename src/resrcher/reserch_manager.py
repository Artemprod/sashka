import asyncio
from datetime import date
from datasourse_for_test.resercch_imirtation import UserResearch

from src.database.database_t import comon_database as reserch_database


def create_research(info) -> UserResearch:
    research = UserResearch(
        research_id="res004",
        title="Анализ времени активности пользователей",
        theme="Временные паттерны активности",
        status=0,
        start_date=date(2024, 9, 1),
        end_date=date(2024, 9, 30),
        user_ids=[401, 402, 403]
    )
    return research


async def start_research(research_id):
    research: UserResearch = reserch_database.get(name=research_id)
    research.status = 1
    # сделать приветсвенную рассылку делегировать коммуникатору
    for user in research.user_ids:
        print(f"Hello user {user}")




def finish_research(research_id):
    research: UserResearch = reserch_database.get(name=research_id)
    research.status = 2


def abort_research(research_id):
    research: UserResearch = reserch_database.get(name=research_id)
    research.status = 4


def add_user(user_id, research_id):
    research: UserResearch = reserch_database.get(name=research_id)
    research.user_ids.append(int(user_id))
    print(f"user {user_id} appended")

def delete_user(user_id, research_id):
    research: UserResearch = reserch_database.get(name=research_id)
    research.user_ids.remove(int(user_id))
    print(f"user {user_id} deleted")


def get_research_info(research_id):
    research: UserResearch = reserch_database.get(name=research_id)
    print(research)





async def main():
    operations = {
        "create_research": {
            "function": create_research,
            "params": ["info"]
        },
        "start_research": {
            "function": start_research,
            "params": ["research_id"]
        },
        "finish_research": {
            "function": finish_research,
            "params": ["research_id"]
        },
        "abort_research": {
            "function": abort_research,
            "params": ["research_id"]
        },
        "add_user": {
            "function": add_user,
            "params": ["user_id", "research_id"]
        },
        "delete_user": {
            "function": delete_user,
            "params": ["user_id", "research_id"]
        },
        "get_research_info": {
            "function": get_research_info,
            "params": ["research_id"]
        }
    }
    research_task = None
    while True:
        command = str(input("Введи название команды: "))
        params = []
        for param in operations[command]['params']:
            params.append(input(f"Введи параметр {param}: "))
        func = operations[command]['function']
        if asyncio.iscoroutinefunction(func):
            if command == "start_research":
                if research_task and not research_task.done():
                    print("Исследование уже запущено")
                else:
                    research_task = asyncio.create_task(func(*params))
            await func(*params)
        else:
            func(*params)




if __name__ == '__main__':
    asyncio.run(main())