from datetime import datetime, timedelta

import pytz

from src.schemas.service.research import ResearchDTOPost


async def validate_data(reserved_dto: ResearchDTOPost) -> ResearchDTOPost:
    start_date = None
    if reserved_dto.timezone_info:
        try:

            timezone = pytz.timezone(reserved_dto.timezone_info)
            if isinstance(reserved_dto.start_date,str) and reserved_dto.start_date == "now":
                start_date = datetime.now(pytz.utc)+timedelta(seconds=1)
            elif isinstance(reserved_dto.start_date, datetime):
                start_date = timezone.localize(reserved_dto.start_date.replace(tzinfo=None))

            reserved_dto.start_date = start_date.astimezone(pytz.utc).replace(tzinfo=None)
            end_date = timezone.localize(reserved_dto.end_date.replace(tzinfo=None))
            reserved_dto.end_date = end_date.astimezone(pytz.utc).replace(tzinfo=None)

        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {reserved_dto.timezone_info}")
    else:
        # Если timezone_info отсутствует, предположим, что время уже в UTC
        reserved_dto.start_date = reserved_dto.start_date.replace(tzinfo=pytz.utc)
        reserved_dto.end_date = reserved_dto.end_date.replace(tzinfo=pytz.utc)

    return reserved_dto