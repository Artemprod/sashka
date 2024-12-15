import pytest

from src.database.postgres import UserStatusEnum
from test_cases import test_cases, StopWordTestCase


class TestStopWordChecker:

    @pytest.mark.parametrize(
        "test_case",
        [
            pytest.param(test_case)
            for test_case in test_cases
        ],
    )
    async def test_stopword(
            self,
            test_case: StopWordTestCase,
            telegram_id,
            load_stop_word_checker,
            mocker
    ):
        status = UserStatusEnum.DONE
        stop_word_checker = load_stop_word_checker
        load_stop_word_checker.repo.user_in_research_repo.short.update_user_status = mocker.AsyncMock(
            return_value=status
        )

        with test_case.expected:
            return_message = await stop_word_checker.monitor_stop_words(
                telegram_id=telegram_id,
                response_message=test_case.income_message
            )
            assert return_message == test_case.return_message
