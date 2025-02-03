import asyncio
from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig


async def clear_jetstream_stream(stream_name: str, nats_url: str = "nats://localhost:4222"):
    # Создаем подключение к NATS
    nc = NATS()
    await nc.connect(nats_url)

    # Инициализируем JetStream
    js = nc.jetstream()

    try:

        # Получаем информацию о стриме

        streams_info = await js.streams_info()

        stream_info = await js.stream_info(stream_name)
        print(f"Стрим найден: {stream_name}, сообщений: {stream_info.state.messages}")

        # Удаляем стрим
        await js.delete_stream(stream_name)
        print(f"Стрим {stream_name} удален.")

        # # Создаем стрим заново (если нужно)
        # await js.add_stream(StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"]))
        # print(f"Стрим {stream_name} создан заново.")

    except Exception as e:
        print(f"Ошибка при очистке стрима: {e}")

    # Закрываем соединение
    await nc.close()


# Запуск асинхронного кода
if __name__ == "__main__":
    stream = "DELAY_MESSAGE_SEND_STREEM"  # Название стрима, который нужно очистить
    asyncio.run(clear_jetstream_stream(stream))