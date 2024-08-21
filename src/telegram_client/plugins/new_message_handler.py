from pyrogram import Client, filters
from pyrogram.types import Message


def custom_filter(_, __, message: Message):
    return "ответ" not in message.text.lower()


@Client.on_message(filters.text)
async def echo(client: Client, message:Message):
    await client.send_message(message.from_user.id, 'Ответ')
