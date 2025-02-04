import asyncio

from faststream import Context
from faststream import Depends
from faststream.nats import NatsMessage
from faststream.nats import NatsRouter
from loguru import logger

from configs.nats_queues import nats_subscriber_researcher_settings
from src.services.research.telegram.inspector import ResearchProcess
from src.subscriber.resercher.dependency.process import get_data_from_headers
from src.subscriber.resercher.utils.reserach import run_research
from src.subscriber.resercher.utils.reserach import task_completion_callback

router = NatsRouter()


@router.subscriber(subject=nats_subscriber_researcher_settings.researches.start_telegram_research)
async def new_message_handler(
    body: str, msg: NatsMessage, context: Context = Context(), research_id: int = Depends(get_data_from_headers)
):
    """Обрабатывает новые входящие сообщения для запуска исследования."""
    processor: ResearchProcess = context.get("processor")

    if not processor:
        logger.error("ResearchProcess not found in context")
        return

    task = asyncio.create_task(run_research(processor, research_id))
    logger.debug("ВЫЗВАЛАСЬ ТАСКА НАЧАЛЬНОГО ЗАПУСКА ИСЛЕДОВАНИЯ ")
    task.add_done_callback(lambda t: task_completion_callback(t, research_id))


@router.subscriber(subject=nats_subscriber_researcher_settings.researches.ban_telegram_research)
async def ban_research_handler(
        body: str,
        msg: NatsMessage,
        context: Context = Context(),
        research_id: int = Depends(get_data_from_headers)
):
    """
    Останавливает и переводит статус исследования в бан
    """
    logger.info(f"Banning research: {research_id}")

    processor: ResearchProcess = context.get("processor")

    if not processor:
        logger.error("ResearchProcess not found in context")
        return

    await processor.ban(
        research_id=research_id,
    )

@router.subscriber(subject=nats_subscriber_researcher_settings.researches.unban_telegram_research)
async def unban_research_handler(
        body: str,
        msg: NatsMessage,
        context: Context = Context(),
        research_id: int = Depends(get_data_from_headers)
):
    """
    Возобновляет исследование
    """
    logger.info(f"Unbanning research: {research_id}")

    processor: ResearchProcess = context.get("processor")

    if not processor:
        logger.error("ResearchProcess not found in context")
        return

    await processor.unban(
        research_id=research_id,
    )
