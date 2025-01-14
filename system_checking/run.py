import asyncio
from typing import List

from configs.nats_queues import nats_distributor_settings, nast_base_settings
from system_checking.nats_chekcer import NatsChecker


async def streams_checking():
    streams: list[FirstMessage | MessageSend] = [nats_distributor_settings.message.first_message_message, nats_distributor_settings.message.send_message]
    url = nast_base_settings.nats_server_url
    nats_checker = NatsChecker(nats_url=url, nats_streams=streams)
    await nats_checker.check()

asyncio.run(streams_checking())

