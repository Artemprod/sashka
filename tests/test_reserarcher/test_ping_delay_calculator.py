import pytest

from src.services.research.telegram.inspector import PingDelayCalculator


@pytest.fixture(scope="function")
async def ping_delay_calculator():
    return PingDelayCalculator()


class TestPingDelayCalculator:
    # TODO: Add more tests
    @pytest.mark.asyncio
    async def test_ping_delay_calculator(self, ping_delay_calculator):
        # assert await ping_delay_calculator.ping_delay_calculator() == 0
        assert True
