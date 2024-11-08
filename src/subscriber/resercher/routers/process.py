import asyncio

from faststream import Context, Depends
from faststream.nats import NatsRouter, NatsMessage
from loguru import logger
from pydantic import BaseModel

from src.services.research.telegram.inspector import ResearchProcess
from src.subscriber.resercher.dependency.process import get_data_from_headers

router = NatsRouter()


# функция-коллбэк, сообщающая о завершении задач

async def run_research(processor: ResearchProcess, research_id: int):
    """Выполняет исследование и логирует результат."""
    try:
        await processor.run(research_id=research_id)
        logger.info(f"Research task {research_id} completed successfully")
    except Exception as e:
        logger.error(f"Failed to run research {research_id}: {e}")
        raise

def task_completion_callback(task: asyncio.Task, research_id: int):
    """Логирует результат выполнения задачи."""
    if task.exception():
        logger.error(f"Research task {research_id} finished with an error: {task.exception()}")
    else:
        logger.info(f"Research task {research_id} finished successfully")

@router.subscriber(subject="research.telegram.start")
async def new_message_handler(
    body: str,
    msg: NatsMessage,
    context: Context = Context(),
    research_id: int = Depends(get_data_from_headers)
):
    """Обрабатывает новые входящие сообщения для запуска исследования."""
    processor: ResearchProcess = context.get("processor")

    if not processor:
        logger.error("ResearchProcess not found in context")
        return

    task = asyncio.create_task(run_research(processor, research_id))
    task.add_done_callback(lambda t: task_completion_callback(t, research_id))