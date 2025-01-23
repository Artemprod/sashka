import pytest
from test_cases import STOP_TEST_CASES, TestDataCases
from utils import status_generator


@pytest.mark.parametrize(
    "test_case",
    [pytest.param(test_case, id=test_case._id) for test_case in STOP_TEST_CASES],
)
async def test_research_end(
    test_case: TestDataCases,
    research_status_stopper,
    mocker,
):
    status_stopper = research_status_stopper
    # генерирует статусы
    generator = status_generator(status_list=test_case.status)
    status_stopper._get_research_current_status = mocker.AsyncMock(side_effect=lambda *args, **kwargs: next(generator))
    result = await status_stopper.monitor_research_status(research_id=test_case.research_id)
    assert result == 1
