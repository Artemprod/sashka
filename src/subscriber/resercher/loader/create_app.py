import sys
from contextlib import asynccontextmanager
from pathlib import Path
from loguru import logger
from environs import Env
from faststream import FastStream, ContextRepo
from faststream.nats import NatsBroker
from src.subscriber.resercher.routers.process import router as process_router
from src.subscriber.resercher.loader.on_startup import initialize_research_processor

env = Env()
env.read_env('.env')
sys.path.append(str(Path(__file__).parent.parent))


@asynccontextmanager
async def lifespan(context: ContextRepo):
    processor: "ResearchProcess" = initialize_research_processor()
    context.set_global("processor", processor)
    logger.info("Start process ")
    yield
    logger.info("Stop process ")


def create_app():
    """Запускает faststream и создает корутину для клиента"""
    broker = NatsBroker(env("NATS_SERVER"))
    broker.include_router(process_router)
    app = FastStream(broker=broker, lifespan=lifespan, title="COMMUNICATOR")
    return app
