from dataclasses import dataclass
from contextlib import nullcontext as does_not_raise
from typing import Union, Any


@dataclass
class TestDataCases:
    income_message: str
    return_message: str
    stop_word: str
    expected: Union[Exception, Any]


test_case_no_stop_word = TestDataCases(
    income_message="Все отлично",
    stop_word="STOP_DIALOG",
    return_message="Все отлично",
    expected=does_not_raise(),
)

test_case_yes_stop_word = TestDataCases(
    income_message="Все отлично STOP_DIALOG",
    stop_word="STOP_DIALOG",
    return_message="Все отлично ",
    expected=does_not_raise(),
)

test_case_lower = TestDataCases(
    income_message="Все отлично stop_dialog",
    stop_word="STOP_DIALOG",
    return_message="Все отлично ",
    expected=does_not_raise(),
)

TEST_CASES = [test_case_no_stop_word, test_case_yes_stop_word, test_case_lower]
