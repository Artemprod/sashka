from pyrogram import filters, Client
from pyrogram.types import Message

from src.telegram_client.client.roters.router import Router

answ_router = Router(name="my_router")

@answ_router.message(filters.text)
async def echo_handler(message: Message, **kwargs):
    client:Client = kwargs['client']
    user = await client.get_chat("aitestings")
    await client.send_message(user.id, text="Салам")