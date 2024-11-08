import os
from typing import Optional, List, Dict

from dotenv import load_dotenv
from pydantic import Field, RedisDsn, field_validator
from pydantic_settings import BaseSettings

from configs.base import BaseConfig


class ResearchService(BaseConfig):
    ...


class ResearchOvercChecker(ResearchService):
    delay_check_interval: int = Field(60, validation_alias='DELAY_BETWEEN_TIME_CHECKING_SECONDS')


class ResearchWordStopper(BaseConfig):
    base_words: List[str] = ["завершено", "исследование завершено", "конец исследования", "окончено", "STOP"]
    stop_words: List[str] = Field(
        default_factory=lambda: ResearchWordStopper.base_words.copy(),
        validation_alias='STOP_WORD_CHECKER_STOP_WORDS_LIST'
    )

    @field_validator("stop_words", mode='before')
    def split_str(cls, field_data):
        # Проверка, является ли значение строкой; если да, разделяем по запятой
        if isinstance(field_data, str):
            return field_data.split(',')
        return field_data


class ResearchPingator(BaseConfig):
    class ResearchPingDelayCalculator(BaseConfig):
        table: Dict[int, int] = Field(default={1: 1, 2: 6, 3: 24, 4: 48},
                                      validation_alias='PINGATOR_DELAY_TABLE_HOURS')

        @field_validator("table",
                         mode='before')
        def parse_dict(cls, value):
            if isinstance(value, str):
                result = {}
                for pair in value.split(','):
                    key, value = pair.split(':')
                    result[int(key)] = int(value)
                return result
            return value

    ping_delay: ResearchPingDelayCalculator = Field(default_factory=ResearchPingDelayCalculator)

    max_pings_messages: int = Field(default=4,
                                    validation_alias='PINGATOR_MAX_PINGS_MESSAGES')
    ping_attempts_multiplier: int = Field(default=2,
                                          validation_alias='PINGATOR_PING_ATTEMPT_MULTIPLIER')
    ping_interval: int = Field(default=10,
                               validation_alias='PINGATOR_PING_INTERVAL_CHEKING')


a = ResearchPingator()
print(a.ping_delay.table)
