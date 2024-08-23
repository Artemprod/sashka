import asyncio

from faststream.nats import NatsBroker

from src.ai_communicator.gpt_comunicator import GptCommunicator
from src.services.openai_api_package.chat_gpt_package.client import GPTClient
from src.services.openai_api_package.chat_gpt_package.model import GPTOptions

OPENAI_API_KEY = 'sk-proj-LSnGH068fmd9T4IcOaluT3BlbkFJbnQKEA40YkcJUb12yLTa'
options = GPTOptions(api_key=OPENAI_API_KEY, model_name='gpt-4o', max_message_count=3, temperature=1,
                     max_return_tokens=1000)

gpt_client = GPTClient(options=options)
comunicator = GptCommunicator(gpt_client=gpt_client)


async def pub():
    async with NatsBroker() as broker:
        message = {'client_id': 'test_b7c995b5-519c-44d4-8b7f-c2fe387eb6a0', "text": "это вот из клиента"}
        await broker.publish(message, subject="send_message")


async def pub_ai():
    async with NatsBroker() as broker:
        response = await comunicator.send_one_message(text="Сгенерируй приветвсенное соообщение")
        message = {'client_id': 'test_a2408592-4eb7-474f-b930-a35071e6fcfe', "text": response}
        await broker.publish(message, subject="send_message")


asyncio.run(pub())
