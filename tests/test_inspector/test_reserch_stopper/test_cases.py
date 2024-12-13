import enum
from dataclasses import dataclass
from typing import Union, Any
from contextlib import nullcontext as does_not_raise

from pytest import raises

from src.database.postgres import ResearchStatusEnum
from src.services.exceptions.research import UserAndResearchInProgressError, UserInProgressError, \
    ResearchStatusInProgressError


@dataclass
class TestDataCases:
    _id: str
    user_in_progres:int
    research_status:enum.Enum
    research_id:int
    expectation: Union[Exception, Any]

# Проверить отработку полного заверешения при условие
# Проверить ошибку UserAndResearchInProgressError
# Проверить ошибку UserInProgressError
# Проверить ошибку ResearchStatusInProgressError

correct_completion = TestDataCases(
    _id="correct completion",
research_id=1,
user_in_progres=0,
research_status=ResearchStatusEnum.DONE,
    expectation=does_not_raise(),
)

exception_user_in_progress_one = TestDataCases(
    _id="exception: 1 user in progres",
research_id=1,
user_in_progres=1,
research_status=ResearchStatusEnum.DONE,
    expectation=raises(UserInProgressError),
)

exception_user_in_progres_ten = TestDataCases(
    _id="exception: 10 users in progres",
research_id=1,
user_in_progres=10,

research_status=ResearchStatusEnum.DONE,
    expectation=raises(UserInProgressError),
)

exception_user_and_research_in_progress = TestDataCases(
    _id="exception: user and research in progress",
research_id=1,
user_in_progres=1,
research_status=ResearchStatusEnum.IN_PROGRESS,
    expectation=raises(UserAndResearchInProgressError),
)

exception_research_in_progress = TestDataCases(
    _id="exception: research in progress",
research_id=1,
user_in_progres=0,
research_status=ResearchStatusEnum.IN_PROGRESS,
    expectation=raises(ResearchStatusInProgressError),
)

TEST_CASES = [correct_completion,
              exception_user_in_progress_one,
              exception_user_in_progres_ten,
              exception_user_and_research_in_progress,
              exception_research_in_progress]