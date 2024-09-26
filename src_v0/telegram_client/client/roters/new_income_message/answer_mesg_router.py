from json import loads

from faststream.nats import NatsBroker
from pyrogram import Client, filters
from pyrogram.types import Message

from src_v0.ai_communicator.gpt_comunicator import GptCommunicator
from src_v0.ai_communicator.model import assistant_aggressive

from src_v0.services.openai_api_package.chat_gpt_package.client import GPTClient
from src_v0.services.openai_api_package.chat_gpt_package.model import GPTOptions
from src_v0.telegram_client.client.roters.new_income_message.filtters import in_research
from src_v0.telegram_client.client.roters.router import Router
from src_v0.utils.convert_to_dict import message_to_dict

answ_router = Router(name="my_router")


#
#
# options=GPTOptions(api_key=OPENAI_API_KEY,model_name='gpt-4o',max_message_count=3,temperature=1,max_return_tokens=1000)
#
# gpt_client = GPTClient(options=options)
# comunicator  = GptCommunicator(gpt_client=gpt_client)
#
# #TODO Все сообщения из отсюда попадают в очередь и уходят в обработчик сообщений от туда они должны распределятся по рабочим
#
# @answ_router.message(filters.create(in_research))
# async def ai_answer(message: Message, **kwargs):
#     print(message)
#     stop_word = "STOP"
#     client: Client = kwargs['client']
#     response = await comunicator.send_response(text=message.text, assistant=assistant_aggressive)
#     if stop_word in response:
#         await change_user_status(user_id=message.from_user.id)
#         response.replace(stop_word, '')
#     await client.send_message(message.from_user.id, text=response)
#
#
# @answ_router.message(not filters.create(in_research))
# async def send_to_disterbuter(message: Message, **kwargs):
#     print(message)
#     client: Client = kwargs['client']
#     await client.send_message(message.from_user.id, text="Ты не в иследовании")
#


# @answ_router.message(not in_research)
# async def send_to_disterbuter(message: Message, **kwargs):
#     # кладем в очередь для отправки
#     data = {'client': kwargs['client'].name, 'message':str(message)}
#     async with NatsBroker() as broker:
#         await broker.publish(message=data, subject="new_message")


# @answ_router.message(hello_filter)
# async def hello(message: Message, **kwargs):
#     client: Client = kwargs['client']
#     await client.send_message(message.from_user.id, 'и тебе тоже привет')

@answ_router.message(filters.text)
async def message_handler(message: Message, **kwargs):
    headers = {
        "User-Id": str(message.from_user.id),
        "Chat-Id": str(message.chat.id)
    }
    async with NatsBroker() as broker:
        try:
            await broker.publish(
                message=message.text,
                subject="message.income.new",
                headers=headers
            )
            print("Сообщение успешно опубликовано в очередь!")


        except Exception as e:
            print(f"Ошибка при публикации сообщения: {e}")
