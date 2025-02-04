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

import asyncio
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

import asyncio
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext


async def clear_all_consumers(nats_url: str, stream_name: str):
    nc = NATS()
    await nc.connect(nats_url)
    js: JetStreamContext = nc.jetstream()

    # Получаем список всех consumers
    consumers_info = await js.consumers_info(stream_name)

    # Исправленный способ получения имен consumers
    consumers = [consumer.name for consumer in consumers_info]

    # Удаляем каждого consumer
    for consumer in consumers:
        try:
            await js.delete_consumer(stream_name, consumer)
            print(f"Deleted consumer: {consumer}")
        except Exception as e:
            print(f"Failed to delete {consumer}: {e}")

    await nc.close()
# Пример вызова
if __name__ == "__main__":
    # stream = "DELAY_MESSAGE_SEND_STREEM"  # Название стрима, который нужно очистить
    # asyncio.run(clear_jetstream_stream(stream))

    asyncio.run(clear_all_consumers("nats://localhost:4222", "SEND_MESSAGE_STREEM"))

# Запуск асинхронного кода
