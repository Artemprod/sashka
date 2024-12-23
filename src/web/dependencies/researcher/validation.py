from datetime import datetime, timedelta

import pytz

from src.schemas.service.research import ResearchDTOPost
from dateutil import parser

#TODO сделать более адекватную валидацию это костыль лучше перенсти возмоджность
# добавлять слова типа now в отделоную категории


async def validate_data(reserved_dto: ResearchDTOPost) -> ResearchDTOPost:
    start_date = reserved_dto.start_date

    if reserved_dto.timezone_info:
        timezone = pytz.timezone(reserved_dto.timezone_info)

        if isinstance(start_date, str) and start_date == "now":
            start_date = datetime.now(pytz.utc) + timedelta(seconds=1)

        elif isinstance(start_date, datetime):
            start_date = timezone.localize(start_date.replace(tzinfo=None))

        elif isinstance(start_date, str) and start_date != "now":
            try:
                # Используем dateutil.parser
                naive_datetime = parser.parse(start_date)
                # Привязать к заданной временной зоне
                start_date = timezone.localize(naive_datetime.replace(tzinfo=None))

            except ValueError as e:
                raise ValueError(f"Invalid date or timezone: {e}")

        if start_date:
            reserved_dto.start_date = start_date.astimezone(pytz.utc).replace(tzinfo=None)

        if reserved_dto.end_date:
            end_date = timezone.localize(reserved_dto.end_date.replace(tzinfo=None))
            reserved_dto.end_date = end_date.astimezone(pytz.utc).replace(tzinfo=None)

    else:
        # Если timezone_info отсутствует, предположим, что время уже в UTC
        if reserved_dto.start_date:
            reserved_dto.start_date = reserved_dto.start_date.replace(tzinfo=pytz.utc)
        if reserved_dto.end_date:
            reserved_dto.end_date = reserved_dto.end_date.replace(tzinfo=pytz.utc)

    return reserved_dto