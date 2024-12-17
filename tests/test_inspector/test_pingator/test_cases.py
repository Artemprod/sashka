# import sys
# from dataclasses import dataclass
# from datetime import datetime
# from pathlib import Path
# from typing import Union, Any, List
# from contextlib import nullcontext as does_not_raise
#
# from src.database.postgres import ResearchStatusEnum
#
#
# @dataclass
# class TestDataCases:
#     _id: str
#     telegram_id: int
#     research_id: int
#     telegram_client_id: int
#     assistant_id: int
#     expectation: Union[Exception, Any]
#
# # Тестирую разное кол-во сообщений  все в одном иследование
# # Тестирую разное кол-во сообщений  все в разных иследованиях
# # Отсутствие промята для пинга
#
#
# one_message = TestDataCases(
#     _id="stop when done",
#     telegram_id=,
#     research_id=,
#     telegram_client_id=,
#     assistant_id=,
#     expectation=does_not_raise())
#
# two_messages = TestDataCases(
#     _id="stop when done",
#     telegram_id=,
#     research_id=,
#     telegram_client_id=,
#     assistant_id=,
#     expectation=does_not_raise())
#
# three_messages = TestDataCases(
#     _id="stop when done",
#     telegram_id=,
#     research_id=,
#     telegram_client_id=,
#     assistant_id=,
#     expectation=does_not_raise())
#
# four_messages = TestDataCases(
#     _id="stop when done",
#     telegram_id=,
#     research_id=,
#     telegram_client_id=,
#     assistant_id=,
#     expectation=does_not_raise())
#
#
# ten_messages = TestDataCases(
#     _id="stop when done",
#     telegram_id=,
#     research_id=,
#     telegram_client_id=,
#     assistant_id=,
#     expectation=does_not_raise())
#
# no_ping_prompt_for_message = TestDataCases(
#     _id="stop when done",
#     telegram_id=,
#     research_id=,
#     telegram_client_id=,
#     assistant_id=,
#     expectation=does_not_raise())
#
# STOP_TEST_CASES = [stop_when_done]
