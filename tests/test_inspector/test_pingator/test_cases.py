import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union, Any, List
from contextlib import nullcontext as does_not_raise

from src.database.postgres import ResearchStatusEnum


@dataclass
class TestDataCases:
    _id: str
    telegram_id: int
    research_id: int
    telegram_client_id: int
    assistant_id: int
    expected_unread_messages: int
    expectation: Union[Exception, Any]


one_message_100 = TestDataCases(
    _id="one_message for user: id 100, in research 100",
    telegram_id=100,
    research_id=100,
    telegram_client_id=100,
    assistant_id=100,
    expected_unread_messages=1,
    expectation=does_not_raise(),
)

two_messages_100 = TestDataCases(
    _id="two_messages for user: id 100, in research 101",
    telegram_id=100,
    research_id=101,
    telegram_client_id=101,
    assistant_id=101,
    expected_unread_messages=2,
    expectation=does_not_raise(),
)

three_messages_100 = TestDataCases(
    _id="three_messages for user: id 100, in research 102",
    telegram_id=100,
    research_id=102,
    telegram_client_id=102,
    assistant_id=102,
    expected_unread_messages=3,
    expectation=does_not_raise(),
)

# ___________________________________
one_message_101 = TestDataCases(
    _id="one_message for user: id 101, in research 100",
    telegram_id=101,
    research_id=100,
    telegram_client_id=100,
    assistant_id=100,
    expected_unread_messages=1,
    expectation=does_not_raise(),
)

two_messages_101 = TestDataCases(
    _id="two_messages for user: id 101, in research 101",
    telegram_id=101,
    research_id=101,
    telegram_client_id=101,
    assistant_id=101,
    expected_unread_messages=2,
    expectation=does_not_raise(),
)

three_messages_101 = TestDataCases(
    _id="three_messages for user: id 101, in research 102",
    telegram_id=101,
    research_id=102,
    telegram_client_id=102,
    assistant_id=102,
    expected_unread_messages=3,
    expectation=does_not_raise(),
)

no_messages_102 = TestDataCases(
    _id="no messages from user: id 102, in research 102",
    telegram_id=102,
    research_id=100,
    telegram_client_id=100,
    assistant_id=100,
    expected_unread_messages=1,
    expectation=does_not_raise(),
)


PING_TEST_CASES = [
    one_message_100,
    two_messages_100,
    three_messages_100,
    one_message_101,
    two_messages_101,
    three_messages_101,
    no_messages_102,
]
