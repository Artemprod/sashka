import asyncio
from random import randint

from datasourse_for_test.resercch_imirtation import UserResearch
from src.ai_communicator.gpt_comunicator import GptCommunicator
from src.ai_communicator.model import AIAssistant, assistant_aggressive, assistant_formal, \
    assistant_informal
from src.database.database_t import comon_database as reserch_database

from src.services.openai_api_package.chat_gpt_package.client import GPTClient
from src.services.openai_api_package.chat_gpt_package.model import GPTOptions



class BaseCommunicator:
    ...
class Communicator(BaseCommunicator):
    conversation_context = {}


    options = GPTOptions(api_key=OPENAI_API_KEY, model_name='gpt-4o', max_message_count=20, temperature=1,
                         max_return_tokens=1000)

    gpt_client = GPTClient(options=options)
    comunicator = GptCommunicator(gpt_client=gpt_client)

    def add_context(self, user_id, data):
        if not user_id in self.conversation_context:
            self.conversation_context[user_id] = []
            self.conversation_context[user_id].append(data)

        else:
            self.conversation_context[user_id].append(data)

    def get_context(self, user_id) -> list:
        print(self.conversation_context)
        return self.conversation_context[user_id] if user_id in self.conversation_context else None

    def load_context(self, user_id):
        return self.conversation_context[user_id]

    async def get_assistant(self, reserch_id) -> AIAssistant:
        if reserch_id == "res001":
            return assistant_formal
        elif reserch_id == "res002":
            return assistant_informal
        elif reserch_id == "res003":
            return assistant_aggressive

    # может возникнуть колизии если пользователь находится в нескольктих иследованиях одновременно
    async def get_recherche(self, user_id) -> UserResearch:
        researches: dict[str, UserResearch] = reserch_database.get_all()
        for recherche_id in researches:
            recherche = researches[recherche_id]
            if user_id in recherche.user_ids:
                return recherche

    async def answer_message(self, user_id, message):
        self.add_context(user_id, {"role": "user", "content": message})
        existing_context: list = self.get_context(user_id)
        recherche = await self.get_recherche(user_id)
        assistant = await self.get_assistant(recherche.research_id)
        print(assistant.name)
        response = await self.comunicator.send_context(context=existing_context, assistant=assistant)
        self.add_context(user_id, {"role": "assistant", "content": response})
        return response

    async def send_first_message(self, user_ids):
        """Делает первую рассылку по пользователем из изледования"""
        allowed_first_message = 2
        delay_between_group = randint(1, 2)
        delay_between_messages = randint(1, 2)
        right_border = 0
        for left_border in range(0, len(user_ids), allowed_first_message):
            if right_border + allowed_first_message > len(user_ids):
                right_border = len(user_ids)
            else:
                right_border = left_border + allowed_first_message
            for user in user_ids[left_border:right_border]:
                print(f"send  message to user {user}")
                await asyncio.sleep(delay_between_messages)

            print("wiait")
            await asyncio.sleep(delay_between_group)



async def main():
    my_id = 101
    while True:
        messsage_from_user = str(input("Введи сообщение: "))
        response = await answer_message(my_id, message=messsage_from_user)
        print(response)


if __name__ == '__main__':
    asyncio.run(main())
