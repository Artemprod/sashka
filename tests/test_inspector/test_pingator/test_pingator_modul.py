import pytest

from src.services.research.telegram.inspector import UserPingator
from test_cases import PING_TEST_CASES, TestDataCases


@pytest.mark.parametrize(
"test_case",
    [
        pytest.param(test_case, id=test_case._id)
        for test_case in PING_TEST_CASES
    ],
)
async def test_unresponde_messages(load_pingator, test_case:TestDataCases):
    #GIVEN пингатор расчитывающий количество неотвеченных сообщений в контексте

    pingator: UserPingator = load_pingator
    #WHEN вызывается метод расчета неотвеченных сообщений
    count = await pingator.count_unresponded_assistant_message(telegram_id=test_case.telegram_id,
                                                       research_id=test_case.research_id,
                                                       telegram_client_id=test_case.telegram_client_id,
                                                       assistant_id=test_case.assistant_id)

    #THEN результат должен быть для каждого контекста разный -> я должен знать точное количесвто неотвеченнх для каждого пользователя
    with test_case.expectation:
        assert count == test_case.expected_unread_messages, "Количество неотвеченных сообщений не совпадает с ожидаемым"

