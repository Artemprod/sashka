import asyncio
from typing import List

import openai
from openai import AsyncOpenAI

from src.services.openai_api_package.chat_gpt_package.model import GPTMessage, GPTOptions


class GPTClient:

    def __init__(self, *, options: GPTOptions):
        self.options = options
        self.client = AsyncOpenAI(api_key=self.options.api_key)
        self._lock = asyncio.Lock()

    async def complete(self, messages: List[GPTMessage], system_message: GPTMessage = None) -> str:
        async with self._lock:
            msg_list = ([system_message] if system_message else []) + messages
            if self.options.max_message_count is not None and len(messages) > self.options.max_message_count:
                msg_list = ([system_message] if system_message else []) + messages[-self.options.max_message_count:]
            gpt_args = {
                "model": self.options.model_name,
                "messages": [{"role": message.role, "content": message.content} for message in msg_list],
                "temperature": self.options.temperature,
                "max_tokens": self.options.max_return_tokens,

            }
            return await self._request(gpt_args)

    async def _request(self, gpt_args: dict) -> str:
        response = await self.client.chat.completions.create(**gpt_args)
        if response.choices:
            response_choice = response.choices[0]  # Получаем первый диалоговый выбор.
            response_message = response_choice.message  # Извлекаем сообщение из выбранного диалога.
            response_text = response_message.content  # Поле 'content' содержит текст ответа.
        else:
            # Обработка случая, когда список 'choices' пуст.
            raise ValueError("No choices returned in the response.")
        return response_text
