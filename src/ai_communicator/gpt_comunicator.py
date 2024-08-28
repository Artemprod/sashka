from typing import List

from src.ai_communicator.exceptions.response import NoResponseFromChatGptSError
from src.ai_communicator.model import AIAssistant
from src.services.openai_api_package.chat_gpt_package.client import GPTClient
from src.services.openai_api_package.chat_gpt_package.model import GPTRole, GPTMessage


class GptCommunicator:

    def __init__(self,
                 gpt_client: GPTClient):
        self.gpt_client = gpt_client

    async def send_response(self, text: str, assistant: AIAssistant) -> str:
        try:
            messages: List[GPTMessage] = [GPTMessage(role=GPTRole.USER, content=text)]
            system_message: GPTMessage = GPTMessage(role=GPTRole.SYSTEM, content=assistant.assistant_prompt)
            result = await self.gpt_client.complete(messages, system_message)
        except Exception as e:
            raise NoResponseFromChatGptSError(exception=e) from e
        else:
            return result

    async def send_context(self, context: list, assistant: AIAssistant) -> str:
        try:
            messages: List[GPTMessage] = [GPTMessage(role=message_dict['role'], content=message_dict['content']) for
                                          message_dict in context]
            system_message: GPTMessage = GPTMessage(role=GPTRole.SYSTEM, content=assistant.assistant_prompt)
            print(messages)
            result = await self.gpt_client.complete(messages, system_message)

        except Exception as e:
            raise NoResponseFromChatGptSError(exception=e) from e
        else:
            return result

    async def send_one_message(self, text: str) -> str:
        try:
            messages: List[GPTMessage] = [
                GPTMessage(role=GPTRole.USER, content=text)]
            system_message: GPTMessage = GPTMessage(role=GPTRole.SYSTEM, content="Генерируй приветсвенное сообщение")
            result = await self.gpt_client.complete(messages, system_message)
        except Exception as e:
            raise NoResponseFromChatGptSError(exception=e) from e
        else:
            return result
