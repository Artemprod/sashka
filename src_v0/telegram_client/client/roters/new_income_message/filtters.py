from pyrogram import filters
from pyrogram.types import Message

from datasourse_for_test.resercch_imirtation import UserResearch
from src_v0.database.database_t import comon_database




def in_research(_, __, message: Message):
    researches = comon_database.get_all()
    for research in researches:
        research: UserResearch = researches[research]
        if message.from_user.id in research.user_ids:
            return True
    return False


def dynamic_data_filter(data):
    async def func(flt, _, query):
        return flt.data == query.data

    # "data" kwarg is accessed with "flt.data" above
    return filters.create(func, data=data)


async def func(_, client, query):
    # r = await client.some_api_method()
    # check response "r" and decide to return True or False
    ...
