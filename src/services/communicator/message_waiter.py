import asyncio

from loguru import logger


class MessageWaiter:
    """
    Класс для управления тайм-аутами ожидания сообщений.

    Этот класс позволяет устанавливать и обновлять таймер, который отсчитывает
    время до отправки ответного сообщения.
    """

    def __init__(self):
        self._current_timeout = None

    async def _timer(self):
        while self._current_timeout > 0:
            await asyncio.sleep(1)
            self._current_timeout -= 1

    def refresh_timer(self, timeout: int):
        """
        Обновляет текущий таймер.
        """
        self._current_timeout = timeout

    async def start_timer(self, timeout: int):
        self._current_timeout = timeout
        await self._timer()
