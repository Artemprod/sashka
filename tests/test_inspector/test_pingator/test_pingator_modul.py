import pytest




#
# from tests.test_inspector.test_pingator.conftest import prepare_database
# from utils import status_generator
#
#
# @pytest.mark.parametrize(
# "test_case",
#     [
#         pytest.param(test_case, id=test_case._id)
#         for test_case in STOP_TEST_CASES
#     ],
# )
# async def test_unresponde_messages(
#         test_case:TestDataCases,
#         load_pingator,
#         mocker,
# ):
#
#     pingator = load_pingator
#
#     await pingator.count_unresponded_assistant_message()

#
#
#     # генерирует статусы
#     # generator = status_generator(status_list=test_case.status)
#     # status_stopper._get_research_current_status = mocker.AsyncMock(side_effect=lambda *args, **kwargs:next(generator) )
#     # result = await status_stopper.monitor_research_status(research_id=test_case.research_id)
#     # assert result==1
#


async def test_unresponde_messages(load_pingator):
    #GIVEN пингатор расчитывающий колдичесвто неотвеченых сообщений в контексте
    #WHEN вызывается метод расчета неотвеченных сообщений
    #THEN результат должен быть для каждого контекста разный -> я должен знать точное количесвто неотвеченнх для каждого пользователя

    assert 1== 1

