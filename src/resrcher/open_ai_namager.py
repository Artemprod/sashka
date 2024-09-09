from src.ai_communicator.gpt_comunicator import GptCommunicator
from src.services.openai_api_package.chat_gpt_package.client import GPTClient
from src.services.openai_api_package.chat_gpt_package.model import GPTOptions


class OpenAiresponser:
    """
    Класс выполняет функцию общения
    отправляет запрос в ИИ получает и отправлет ответ клиенту

    """
    conversation_context = {}

    options = GPTOptions(api_key="OPENAI_API_KEY", model_name='gpt-4o', max_message_count=20, temperature=1,
                         max_return_tokens=1000)

    gpt_client = GPTClient(options=options)
    comunicator = GptCommunicator(gpt_client=gpt_client)

    def __init__(self):
        self.settings = {}

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
