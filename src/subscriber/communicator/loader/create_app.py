import sys
from contextlib import asynccontextmanager
from pathlib import Path
from environs import Env
from faststream import FastStream, ContextRepo
from faststream.nats import NatsBroker
from src.subscriber.communicator.routers.message import router as message_router

from src.subscriber.communicator.loader.on_startup import initialize_communicator

env = Env()
env.read_env('.env')
sys.path.append(str(Path(__file__).parent.parent))


@asynccontextmanager
async def lifespan(context: ContextRepo):
    communicator: "TelegramCommunicator" = initialize_communicator()
    context.set_global("communicator", communicator)
    yield


def create_app():
    """Запускает faststream и создает корутину для клиента"""
    broker = NatsBroker(env("NATS_SERVER"))
    broker.include_router(message_router)
    app = FastStream(broker=broker, lifespan=lifespan, title="COMMUNICATOR")
    return app
