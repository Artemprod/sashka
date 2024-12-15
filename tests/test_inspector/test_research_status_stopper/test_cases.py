import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union, Any, List
from contextlib import nullcontext as does_not_raise

from src.database.postgres import ResearchStatusEnum


@dataclass
class TestDataCases:
    _id: str
    research_id:int
    status:list
    expectation: Union[Exception, Any]

# Тестирую процесс перехода между статусами
# ожидание - прогресс - готово
# ожидание - прогресс - отмена
# ожидание - прогресс - пауза

stop_when_done = TestDataCases(
    _id="stop when done",
    research_id=123,
    status=[ResearchStatusEnum.WAIT.value,ResearchStatusEnum.IN_PROGRESS.value, ResearchStatusEnum.DONE.value,],
    expectation=does_not_raise(),
)

stop_when_aborted = TestDataCases(
    _id="stop when aborted",
    research_id=123,
    status=[ResearchStatusEnum.WAIT.value, ResearchStatusEnum.IN_PROGRESS.value, ResearchStatusEnum.ABORTED.value,],
    expectation=does_not_raise(),
)


stop_when_pause = TestDataCases(
    _id="stop when pause",
    research_id=123,
    status=[ResearchStatusEnum.IN_PROGRESS.value, ResearchStatusEnum.WAIT.value,ResearchStatusEnum.PAUSE.value,],
    expectation=does_not_raise(),
)


STOP_TEST_CASES = [stop_when_done,stop_when_aborted,stop_when_pause]
