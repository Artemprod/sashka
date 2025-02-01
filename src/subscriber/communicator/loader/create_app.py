from contextlib import asynccontextmanager

from faststream import ContextRepo
from faststream import FastStream
from faststream.nats import NatsBroker

from configs.nats_queues import nast_base_settings
from src.services.scheduler.manager import AsyncPostgresSchedularManager
from src.subscriber.communicator.loader.on_startup import initialize_communicator, initialize_schedular
from src.subscriber.communicator.routers.commands import router as command_router
from src.subscriber.communicator.routers.message import router as message_router


@asynccontextmanager
async def lifespan(context: ContextRepo):
    scheduler:AsyncPostgresSchedularManager= initialize_schedular()
    scheduler.start()
    communicator: "TelegramCommunicator" = initialize_communicator(scheduler=scheduler)
    context.set_global("communicator", communicator)
    yield
    scheduler.shutdown()

def create_app():
    """Запускает faststream и создает корутину для клиента"""
    broker = NatsBroker(nast_base_settings.nats_server_url)
    broker.include_router(message_router)
    broker.include_router(command_router)
    app = FastStream(broker=broker, lifespan=lifespan, title="COMMUNICATOR")
    return app
