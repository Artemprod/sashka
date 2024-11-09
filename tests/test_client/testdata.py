from contextlib import nullcontext as does_not_raise
from dataclasses import dataclass
from typing import Any
from typing import Union

import pytest
from pyrogram.errors import ApiIdInvalid
from pyrogram.errors import PasswordHashInvalid
from pyrogram.errors import PhoneNumberInvalid

from src.distributor.telegram_client.exceptions import MaxAttemptsExceededError

test_api_id = '17349'
test_api_hash = "344583e45741c457fe1862106095a5eb"
phone_number = '9996611112'


@dataclass
class TestDataCases:
    _id: str
    name: str
    test_phone: str
    phone_code: str
    test_password: str
    api_id: str
    api_hash: str
    expectation: Union[Exception, Any]


TEST_CASES = [
    TestDataCases(_id="2auth test",
                  name="test",
                  test_phone="9996601212",
                  phone_code="00000",
                  test_password="89671106966",
                  api_id=test_api_id,
                  api_hash=test_api_hash,
                  expectation=does_not_raise()),

    TestDataCases(_id="wrong 2auth ",
                  name="test",
                  test_phone="9996601212",
                  phone_code="00000",
                  test_password="896711069",
                  api_id=test_api_id,
                  api_hash=test_api_hash,
                  expectation=pytest.raises(PasswordHashInvalid)),
    TestDataCases(
        _id="no 2auth test",
        name="test",
        test_phone=phone_number,
        phone_code=phone_number[6] * 5,
        test_password="",
        api_id=test_api_id,
        api_hash=test_api_hash,
        expectation=does_not_raise()
    ),
    TestDataCases(
        _id="Wrong phone code",
        name="test",
        test_phone=phone_number,
        phone_code=phone_number[3] * 5,
        test_password="",
        api_id=test_api_id,
        api_hash=test_api_hash,
        expectation=pytest.raises(MaxAttemptsExceededError)),

    TestDataCases(
        _id="wrong phone number",
        name="test",
        test_phone='9976311111',
        phone_code="11111",
        test_password="",
        api_id=test_api_id,
        api_hash=test_api_hash,
        expectation=pytest.raises(PhoneNumberInvalid)
    ),
    TestDataCases(
        _id="Wrong api id",
        name="test",
        test_phone=phone_number,
        phone_code=phone_number[6] * 5,
        test_password="",
        api_id='11111',
        api_hash=test_api_hash,
        expectation=pytest.raises(ApiIdInvalid)),
    TestDataCases(
        _id="Wrong hash",
        name="test",
        test_phone=phone_number,
        phone_code=phone_number[6] * 5,
        test_password="",
        api_id=test_api_id,
        api_hash="344583e45741c457fe1862106095a54b",
        expectation=pytest.raises(ApiIdInvalid)),
]
