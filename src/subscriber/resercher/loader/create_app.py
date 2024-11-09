import sys
from contextlib import asynccontextmanager
from pathlib import Path
from loguru import logger
from environs import Env
from faststream import FastStream, ContextRepo
from faststream.nats import NatsBroker

from configs.nats_queues import nast_base_settings
from src.subscriber.resercher.routers.process import router as process_router
from src.subscriber.resercher.loader.on_startup import initialize_research_processor

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
    broker = NatsBroker(nast_base_settings.nats_server_url)
    broker.include_router(process_router)
    app = FastStream(broker=broker, lifespan=lifespan, title="COMMUNICATOR")
    return app
