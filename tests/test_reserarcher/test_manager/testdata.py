from contextlib import nullcontext as does_not_raise
from dataclasses import dataclass
from typing import Any
from typing import Union

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from src.schemas.service.research import ResearchDTOPost


@dataclass
class ResearchDTOPostCases:
    research_dto: ResearchDTOPost
    expectation: Union[Exception, Any]


TEST_CASES = [
    # Successful case
    ResearchDTOPostCases(
        research_dto=ResearchDTOPost(
            research_uuid="test_uuid_1",
            name='Test Case 1',
            title="Test Title 1",
            theme="Test Theme 1",
            descriptions="Test Description 1",
            additional_information="Test Additional Information 1",
            assistant_id=1,
            examinees_ids=[1, 2, 3],
            examinees_user_names=["user1", "user2", "user3"]
        ),
        expectation=does_not_raise()
    ),
    ResearchDTOPostCases(
        research_dto=ResearchDTOPost(
            research_uuid="test_uuid_2",
            name='Test Case 2',
            title="Test Title 2",
            theme="Test Theme 2",
            descriptions="Test Description 2",
            additional_information="Test Additional Information 2",
            assistant_id=3,
            examinees_ids=[1, 2, 3],
            examinees_user_names=["user4", "user5", "user6"]
        ),
        expectation=pytest.raises(IntegrityError)
    ),
    # Case expecting a TypeError
    ResearchDTOPostCases(
        research_dto=ResearchDTOPost(
            research_uuid="test_uuid_3",
            name='Test Case 3',
            title="Test Title 3",
            descriptions="Test Description 3",
            additional_information="Test Additional Information 3",
            assistant_id=1,
            examinees_ids=[1, 2, 3],
            examinees_user_names=["user7", "user8", "user9"]
        ),
        expectation=does_not_raise()
    ),
    # Assistant doesn't exist
    ResearchDTOPostCases(
        research_dto=ResearchDTOPost(
            research_uuid="test_uuid_4",
            name='Test Case 4',
            title="Test Title 4",
            theme="Test Theme 4",
            descriptions="Test Description 4",
            additional_information="Test Additional Information 4",
            assistant_id=2,
            examinees_ids=[4, 5, 6],
            examinees_user_names=["user10", "user11", "user12"]
        ),
        expectation=pytest.raises(IntegrityError)
    ),
    # Case expecting an AssertionError
    ResearchDTOPostCases(
        research_dto=ResearchDTOPost(
            research_uuid="test_uuid_5",
            name='Test Case 5',
            title="Test Title 5",
            theme="Test Theme 5",
            descriptions="",  # Empty description should not error
            additional_information="Test Additional Information 5",
            assistant_id=1,
            examinees_ids=[7, 8, 9],
            examinees_user_names=["user13", "user14", "user15"]
        ),
        expectation=does_not_raise()
    ),
]
