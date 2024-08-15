from pyrogram import Client, filters



@Client.on_message(filters.text)
async def echo(client, message):
    await message.reply(message.text)


