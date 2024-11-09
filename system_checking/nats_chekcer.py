from nats.js.api import StreamConfig
import asyncio



from configs.nats_queues import nats_distributor_settings, nast_base_settings

from nats.aio.client import Client as NATS
from nats.js.errors import NotFoundError


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
                print(f"Updated stream '{stream_name}' with new subjects: {new_subjects - existing_subjects}")
            else:
                print(f"All subjects for stream '{stream_name}' already exist.")

        except NotFoundError:
            # Создание нового стрима, если он не существует
            print(f"Stream '{stream_name}' is being created.")
            stream_config = StreamConfig(
                name=stream_name,
                subjects=subjects,
                retention=retention_policy,
                storage=storage_type,
                allow_direct=allow_direct
            )
            await js.add_stream(config=stream_config)
            print(f"Stream '{stream_name}' created successfully with subjects: {subjects}")


