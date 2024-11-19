from pyrogram import filters
from pyrogram.types import Message




def dynamic_data_filter(data):
    async def func(flt, _, query):
        return flt.data == query.data

    # "data" kwarg is accessed with "flt.data" above
    return filters.create(func, data=data)


async def func(_, client, query):
    # r = await client.some_api_method()
    # check response "r" and decide to return True or False
    ...
