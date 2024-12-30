from datetime import datetime

from src.schemas.service.research import ResearchDTOFull


class CyclePingAttemptCalculator:
    def __init__(self, research_info: ResearchDTOFull, attempt_multiplicative: int):
        self.start_date = self._validate_and_parse_date(research_info.start_date)
        self.end_date = self._validate_and_parse_date(research_info.end_date)
        self._attempt_multiplicative = attempt_multiplicative

    @staticmethod
    def _validate_and_parse_date(date_input) -> datetime:
        """Преобразует строку или объект datetime в объект datetime без информации о временной зоне."""
        if isinstance(date_input, datetime):
            return date_input.replace(tzinfo=None)
        elif isinstance(date_input, str):
            try:
                parsed_date = datetime.strptime(date_input, "%Y-%m-%d %H:%M:%S")
                return parsed_date
            except ValueError as e:
                raise ValueError(f"Invalid date format: {date_input}. Expected format: YYYY-MM-DD HH:MM:SS.") from e
        else:
            raise TypeError("Date input must be a string or a datetime object.")

    def calculate_max_attempts(self) -> int:
        """Вычисляет максимальное количество попыток на основе разницы во времени между датами."""
        time_difference = self.end_date - self.start_date
        max_attempt = int(time_difference.total_seconds() / 60) * self._attempt_multiplicative
        return max_attempt
