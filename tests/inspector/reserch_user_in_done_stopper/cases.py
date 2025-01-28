import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union, Any
from contextlib import nullcontext as does_not_raise


@dataclass
class TestDataCases:
    _id: str
    research_id: int
    users: int
    expectation: Union[Exception, Any]


one_hundred_users = TestDataCases(
    _id="one_hundred_users",
    research_id=123,
    users=100,
    expectation=does_not_raise(),
)


TEST_CASES = [one_hundred_users]
