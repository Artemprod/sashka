import pytest

from src.database.repository.storage import RepoStorage
from src.services.research.telegram.inspector import ResearchStopper, StopWordChecker


@pytest.fixture
def telegram_id():
    return 1234


@pytest.fixture
def load_repo(mocker):
    return mocker.Mock(spec=RepoStorage)


@pytest.fixture
def load_stopper(mocker):
    return mocker.Mock(spec=ResearchStopper)


@pytest.fixture
def load_stop_word_checker(load_repo,load_stopper,):
    return  StopWordChecker(stopper=load_stopper,repo=load_repo)


@pytest.mark.asyncio
async def test_summarize_calls_gpt_client(self, gpt_summarizer, mock_gpt_client, assistant, mocker, test_case):
    mock_gpt_client.complete = mocker.AsyncMock(return_value=test_case.expected_response)
    user_message = assistant.user_prompt + test_case.transcribed_text
    system_message = assistant.assistant_prompt