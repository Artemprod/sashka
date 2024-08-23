import asyncio

from datasourse_for_test.resercch_imirtation import UserResearch
from src.ai_communicator.gpt_comunicator import GptCommunicator
from src.ai_communicator.model import AIAssistant, assistant_aggressive, assistant_formal, \
    assistant_informal
from src.database.database_t import comon_database as reserch_database
from src.services.openai_api_package.chat_gpt_package.client import GPTClient
from src.services.openai_api_package.chat_gpt_package.model import GPTOptions

conversation_context = {}

OPENAI_API_KEY = 'sk-proj-LSnGH068fmd9T4IcOaluT3BlbkFJbnQKEA40YkcJUb12yLTa'
options = GPTOptions(api_key=OPENAI_API_KEY, model_name='gpt-4o', max_message_count=3, temperature=1,
                     max_return_tokens=1000)

gpt_client = GPTClient(options=options)
comunicator = GptCommunicator(gpt_client=gpt_client)


def add_context(user_id, data):
    if not user_id in conversation_context:
        conversation_context[user_id] = []
        conversation_context[user_id].append(data)

    else:
        conversation_context[user_id].append(data)


def get_context(user_id) -> list:
    print(conversation_context)
    return conversation_context[user_id] if user_id in conversation_context else None


def load_context(user_id):
    return conversation_context[user_id]


async def get_assistant(reserch_id) -> AIAssistant:
    if reserch_id == "res001":
        return assistant_formal
    elif reserch_id == "res002":
        return assistant_informal
    elif reserch_id == "res003":
        return assistant_aggressive



# может возникнуть колизии если пользователь находится в нескольктих иследованиях одновременно
async def get_recherche(user_id) -> UserResearch:
    researches: dict[str, UserResearch] = reserch_database.get_all()
    for recherche_id in researches:
        recherche = researches[recherche_id]
        if user_id in recherche.user_ids:
            return recherche


async def answer_message(user_id, message):
    add_context(user_id, {"role": "user", "content": message})
    existing_context: list = get_context(user_id)
    recherche = await get_recherche(user_id)
    assistant = await get_assistant(recherche.research_id)
    print(assistant.name)
    response = await comunicator.send_response(text=f"{existing_context} {message}", assistant=assistant)
    add_context(user_id, {"role": "assistant", "content": response})
    return response


async def main():
    my_id = 101
    while True:
        messsage_from_user = str(input("Введи сообщение: "))
        response = await answer_message(my_id, message=messsage_from_user)
        print(response)


if __name__ == '__main__':
    asyncio.run(main())
