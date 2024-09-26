import openai
from loguru import logger

from project_configs.configs import WhisperConfigs


class WhisperClient:
    def __init__(self,
                 api_key,
                 configs:WhisperConfigs):
        """
        Конструктор класса.
        Инициализация API ключа и создание асинхронного клиента.
        """
        self.configs = configs

        openai.api_key = api_key
        self.client = openai.AsyncClient(api_key=api_key)

        # Инициализация базовых промптов
        self.base_prompts = {
            'bad_word': "Эм..Ага, так, да,да...",
            'punctuation': "Добрый день, спасибо что пришли! Сегодня..."
        }

    async def load_prompts(self):
        return ', '.join(self.base_prompts.values())

    async def whisper_compile(self, file_path: str, additional_prompts: str = "", ):
        with open(file_path, "rb") as audio_file:
            whisper_args = {
                "model": self.configs.whisper_model_version,
                "prompt": f"{await self.load_prompts()}, {additional_prompts}",
                "file": audio_file,
                "language": self.configs.whisper_language,
                "temperature": self.configs.whisper_model_temperature,
            }

            return await self.send_request(whisper_args)

    async def send_request(self, whisper_args: dict) -> str:
        response = await self.client.audio.transcriptions.create(**whisper_args)
        if response.text:
            logger.info("response from whisper_package received")
        return response.text

