import pytest

from src.services.research.telegram.inspector import StopWordChecker


@pytest.fixture(scope="function")
def stop_word_checker(research_stopper, repo_storage):
    yield StopWordChecker(research_stopper, repo_storage, stop_phrases=["стоп", "стоп-слово", "все спасибо"])


@pytest.mark.asyncio
class TestStopWordChecker:
    @pytest.mark.parametrize(
        "message",
        ["Спасибо большое вам, все спасибо", "Не используйте стоп", "Не используйте стоп-слово"]
    )
    async def test_contains_stop_word(self, stop_word_checker, message):
        result = await stop_word_checker._contains_stop_phrase(message)
        assert result == True

    @pytest.mark.parametrize(
        "message",
        ["Спасибо большое вам", "Не используйте -слово", "Не используйте все вместе"]
    )
    async def test_not_contains_stop_word(self, stop_word_checker, message):
        result = await stop_word_checker._contains_stop_phrase(message)
        assert result != True

    @pytest.mark.parametrize(
        "research_id, response_message, user_id, answer",
        [(1, "стоп", 30, True), (1, "стоп-слово", 27, True), (1, "все спасибо", 28, True)]
    )
    async def test_stop_word_checker(self, stop_word_checker, research_id, response_message, user_id, answer):
        result = await stop_word_checker.check_for_stop_words(research_id, response_message, user_id)
        assert result == answer

    @pytest.mark.parametrize(
        "new_stop_phrase",
        [["новое стоп-слово", "новое стоп"], ["другое стоп слово", "другое стоп"]]
    )
    async def test_check_update_stop_phrase(self, stop_word_checker, new_stop_phrase):
        await stop_word_checker.update_stop_phrases(new_phrases=new_stop_phrase)
        assert stop_word_checker.stop_phrases == new_stop_phrase
