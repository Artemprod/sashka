import pytest
from test_cases import TEST_CASES, TestDataCases


@pytest.mark.parametrize(
    "test_case",
    [pytest.param(test_case, id=test_case._id) for test_case in TEST_CASES],
)
async def test_research_end(
    test_case: TestDataCases,
    load_research_stopper,
    mocker,
):
    # GIVEN
    # Mock
    research_stopper = load_research_stopper
    research_stopper._update_research_status = mocker.AsyncMock(return_value=None)
    research_stopper._update_user_statuses = mocker.AsyncMock(return_value=None)
    research_stopper._get_users_in_research = mocker.AsyncMock(return_value=None)

    research_stopper._get_users_in_progress = mocker.AsyncMock(return_value=test_case.user_in_progres)
    research_stopper._get_research_status = mocker.AsyncMock(return_value=test_case.research_status)

    # WHEN
    with test_case.expectation:
        result = await research_stopper.complete_research(research_id=test_case.research_id)
        # THEN
        assert result == 1
