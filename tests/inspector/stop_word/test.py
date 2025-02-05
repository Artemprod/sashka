import pytest

from src.database.postgres import UserStatusEnum
from . cases import TEST_CASES,TestDataCases



class TestStopWordChecker:
    @pytest.mark.parametrize(
        "test_case",
        [pytest.param(test_case) for test_case in TEST_CASES],
    )
    async def test_stopword(self, test_case: TestDataCases, telegram_id, load_stop_word_checker, mocker):
        status = UserStatusEnum.DONE
        stop_word_checker = load_stop_word_checker

        stop_word_checker.repo.user_in_research_repo.short.update_user_status = mocker.AsyncMock(
            return_value=status
        )
        stop_word_checker._get_stop_phrase = mocker.AsyncMock(
            return_value=test_case.stop_word
        )


        with test_case.expected:
            return_message = await stop_word_checker.monitor_stop_words(
                telegram_id=telegram_id,
                response_message=test_case.income_message
            )
            assert return_message == test_case.return_message
