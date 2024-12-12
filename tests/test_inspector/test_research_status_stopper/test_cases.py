import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union, Any
from contextlib import nullcontext as does_not_raise

from src.database.postgres import ResearchStatusEnum


@dataclass
class TestDataCases:
    _id: str
    research_id:int
    status:str
    expectation: Union[Exception, Any]


#____ не должен остановиться
in_progres_status = TestDataCases(
    _id="IN_PROGRESS STATUS",
    research_id=123,
    status=ResearchStatusEnum.IN_PROGRESS.value,
    expectation=does_not_raise(),
)

wait_status = TestDataCases(
    _id="WAIT STATUS",
    research_id=123,
    status=ResearchStatusEnum.WAIT.value,
    expectation=does_not_raise(),
)

#____ Должен остановиться
done_status = TestDataCases(
    _id="DONE STATUS",
    research_id=123,
    status=ResearchStatusEnum.DONE.value,
    expectation=does_not_raise(),
)

aborted_status = TestDataCases(
    _id="ABORTED STATUS",
    research_id=123,
    status=ResearchStatusEnum.ABORTED.value,
    expectation=does_not_raise(),
)

pause_status = TestDataCases(
    _id="PAUSE STATUS",
    research_id=123,
    status=ResearchStatusEnum.PAUSE.value,
    expectation=does_not_raise(),
)

STOP_TEST_CASES = [done_status,aborted_status,pause_status]
DONT_STOP_TEST_CASES = [in_progres_status,wait_status]