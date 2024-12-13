from dataclasses import dataclass
from contextlib import nullcontext as does_not_raise
from typing import Union, Any


@dataclass
class StopWordTestCase:
    income_message: str
    return_message:str
    stop_word: str
    expected: Union[Exception, Any]


test_case_no_stop_word = StopWordTestCase(
    income_message="Все отлично",
    stop_word="STOP",
    return_message="Все отлично",
    expected=does_not_raise(),
)

test_case_yes_stop_word = StopWordTestCase(
    income_message="Все отлично STOP",
    stop_word="STOP",
    return_message="Все отлично ",
    expected=does_not_raise(),
)

test_case_lower = StopWordTestCase(
    income_message="Все отлично stop",
    stop_word="STOP",
    return_message="Все отлично ",
    expected=does_not_raise(),
)

test_cases = [test_case_no_stop_word, test_case_yes_stop_word, test_case_lower]
