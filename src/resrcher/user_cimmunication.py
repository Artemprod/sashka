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
    """
    Класс выполняет функцию общения
    отправляет запрос в ИИ получает и отправлет ответ клиенту

    """


    def __init__(self):
        self.settings = {}



    async def answer_message(self, user_id, message):
        ...

    # TODO Вот тут логика отправки сообщений кусками генерируем сообщение кладем в чередь пачками
    async def send_first_message(self, user_ids):
        """Делает первую рассылку по пользователем из изледования
        тот медот не знает о сущестоввании ИИ он только отправляет завпрос, получет ответ и перенаправлет в клиента
        Идея по реализации: использвоание jetstreem для рассылки через интервыал


        1. Получает данные о пользователи
            если есть лданные если нет
        2. получает ассистента
            еесли есть асистент если нет
        3. отправлет запрос к ИИ
        4. Получает ответ
            если есть ответ если нет ошибка
        5. Отправлет запрос на отправку сообщение клинету
            если получилось отправить если нет ошибка


        """
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
