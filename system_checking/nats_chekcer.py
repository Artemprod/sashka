import asyncio

from nats.aio.client import Client as NATS
from nats.aio.errors import ErrNoServers, ErrConnectionClosed, ErrTimeout
from nats.js.api import StreamConfig
from nats.js.errors import NotFoundError
from loguru import logger

class NatsChecker:
    def __init__(self, nats_url, nats_streams: list):
        self.nats_streams = nats_streams
        self.nats_url = nats_url

    async def check(self):
        nc = NATS()
        await nc.connect(self.nats_url)

        for stream in self.nats_streams:
            await self.create_or_update_stream(nc, stream_name=stream.stream,
                                               subjects=[stream.subject],
                                               retention_policy=stream.retention_policy,
                                               storage_type=stream.storage_type,
                                               allow_direct=stream.allow_direct)

    async def create_or_update_stream(self, nc, stream_name, subjects, retention_policy, storage_type, allow_direct):
        js = nc.jetstream()
        try:
            # Проверка существования стрима
            stream_info = await js.stream_info(stream_name)
            existing_subjects = set(stream_info.config.subjects)
            new_subjects = set(subjects)

            # Проверка и добавление отсутствующих сабджектов
            if not new_subjects.issubset(existing_subjects):
                updated_subjects = list(existing_subjects.union(new_subjects))
                stream_config = StreamConfig(
                    name=stream_name,
                    subjects=updated_subjects,
                    retention=retention_policy,
                    storage=storage_type,
                    allow_direct=allow_direct
                )

                await js.update_stream(name=stream_name, config=stream_config)
                logger.info(f"Updated stream '{stream_name}' with new subjects: {new_subjects - existing_subjects}")
            else:
                logger.info(f"All subjects for stream '{stream_name}' already exist.")

        except NotFoundError:
            # Создание нового стрима, если он не существует
            logger.info(f"Stream '{stream_name}' is being created.")
            stream_config = StreamConfig(
                name=stream_name,
                subjects=subjects,
                retention=retention_policy,
                storage=storage_type,
                allow_direct=allow_direct
            )
            await js.add_stream(config=stream_config)
            logger.info(f"Stream '{stream_name}' created successfully with subjects: {subjects}")

    async def check_connection(self):
        nc = NATS()
        max_retries = 3
        retry_count = 0
        connected = False

        while not connected and retry_count < max_retries:
            try:
                logger.debug(f"Attempting to connect to NATS at {self.nats_url} (Attempt {retry_count + 1})")
                await nc.connect(self.nats_url, connect_timeout=5)
                logger.info(f"Successfully connected to NATS at {self.nats_url}")
                connected = True
            except ErrNoServers as e:
                logger.error(f"No servers available to connect to: {e}")
            except ErrConnectionClosed as e:
                logger.error(f"Connection was closed unexpectedly: {e}")
            except ErrTimeout as e:
                logger.error(f"Connection attempt timed out: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while trying to connect: {e}")

            if not connected:
                retry_count += 1
                logger.debug("Retrying connection...")
                await asyncio.sleep(2)  # Wait before retrying
            else:
                break

        if not connected:
            logger.error(f"Failed to connect to NATS after {max_retries} attempts")

        await nc.close()
