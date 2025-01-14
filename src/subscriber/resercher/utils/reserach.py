import asyncio

from loguru import logger

from src.services.research.telegram.inspector import ResearchProcess


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
