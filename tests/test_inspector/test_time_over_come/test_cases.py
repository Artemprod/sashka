import sys
from dataclasses import dataclass
from datetime import datetime
from enum import EnumType
from pathlib import Path
from typing import Union, Any
from contextlib import nullcontext as does_not_raise



@dataclass
class TestDataCases:
    _id: str
    research_id:int
    start_date: datetime
    end_date: datetime
    time_zone:str
    expectation: Union[Exception, Any]

# Остановка точно по времени минута в минуту
# Когда дата конца раньше чем дата начала
# Когда дата конца такая же как дата начала
# Разные тайм зоны ( тайм зона должна быть одинакова )

precise_end_1 = TestDataCases(
    _id="13:00:00",
    research_id=123,
    start_date=datetime.strptime("2024-12-11T12:00:00", '%Y-%m-%dT%H:%M:%S'),
    end_date=datetime.strptime("2024-12-11T13:00:00", '%Y-%m-%dT%H:%M:%S'),
    time_zone="UTC",
    expectation=does_not_raise(),
)

precise_end_2 = TestDataCases(
    _id="13:12:31",
    research_id=123,
    start_date=datetime.strptime("2024-12-11T12:00:00", '%Y-%m-%dT%H:%M:%S'),
    end_date=datetime.strptime("2024-12-11T13:12:31", '%Y-%m-%dT%H:%M:%S'),
    time_zone="UTC",
    expectation=does_not_raise(),
)


TEST_CASES = [precise_end_1,precise_end_2]