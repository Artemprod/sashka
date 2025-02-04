from datetime import timedelta

import pytest


from . cases import TEST_CASES, TestDataCases
from . utils import user_status_generator


# Создаем генератор времени, который повышает текущее время на 1 секунду при каждом вызове
def time_generator(start_time):
    current_time = start_time
    while True:
        yield current_time
        current_time += timedelta(seconds=1)


@pytest.mark.parametrize(
    "test_case",
    [pytest.param(test_case, id=test_case._id) for test_case in TEST_CASES],
)
async def test_research_end(
    test_case: TestDataCases,
    load_user_done,
    mocker,
):
    user_status_stopper = load_user_done
    generator = user_status_generator(test_case.users)
    user_status_stopper._get_users_in_progress = mocker.AsyncMock(side_effect=lambda *args, **kwargs: next(generator))
    result = await user_status_stopper.monitor_user_status(research_id=test_case.research_id)
    with test_case.expectation:
        assert result == 1, "The error:Cant stop user in progrtes"
