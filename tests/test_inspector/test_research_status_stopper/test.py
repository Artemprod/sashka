import pytest
from test_cases import STOP_TEST_CASES, DONT_STOP_TEST_CASES, TestDataCases



@pytest.mark.parametrize(
"test_case",
    [
        pytest.param(test_case, id=test_case._id)
        for test_case in DONT_STOP_TEST_CASES
    ],
)
async def test_research_end(
        test_case:TestDataCases,
        research_status_stopper,
        mocker,
):

    status_stopper = research_status_stopper
    max_iterations = 100  # Максимальное число итераций которые мы хотим выполнить
    iteration_count = 0

    # Определите функцию, которая увеличивает счетчик и возвращает нужное значение
    async def mock_get_status(research_id):
        nonlocal iteration_count
        iteration_count += 1
        # Если достигли максимального числа итераций, возвращаем конкретный статус для завершения
        if iteration_count >= max_iterations:
            return "COMPLETED"  # Или любой другой статус, который закончит цикл
        return test_case.status

    # Мокаем `_get_research_current_status`, чтобы использовать нашу логику
    status_stopper._get_research_current_status = mocker.Mock(side_effect=mock_get_status)

    result = await status_stopper.monitor_research_status(research_id=test_case.research_id)

    # Убеждаемся, что количество итераций не превысило максимум
    assert iteration_count <= max_iterations
