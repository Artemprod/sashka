from datetime import timedelta

import pytest
from pytest_mock import mocker
from utils import time_generator
from test_cases import TEST_CASES, TestDataCases




@pytest.mark.parametrize(
"test_case",
    [
        pytest.param(test_case, id=test_case._id)
        for test_case in TEST_CASES
    ],
)
async def test_research_end(
        test_case:TestDataCases,
        load_time_stopper,
        mocker,
):

    test_time = test_case.end_date - timedelta(seconds=5)
    generator = time_generator(test_time)
    # Используем side_effect для изменения времени в каждом вызове

    time_stopper = load_time_stopper
    time_stopper._get_research_end_date = mocker.AsyncMock(return_value=test_case.end_date)

    mock_datetime = mocker.patch("src.services.research.telegram.inspector.datetime")
    mock_datetime.now.side_effect = lambda *args, **kwargs: next(generator)

    result = await time_stopper.monitor_time_completion(research_id=test_case.research_id)
    with test_case.expectation:
        assert result==1, "The error:Cant stop with time over"
