import sys
from pathlib import Path
from typing import Dict
from typing import List

from pydantic import Field
from pydantic import field_validator

from configs.base import BaseConfig

sys.path.append(str(Path(__file__).parent.parent))


class ResearchService(BaseConfig):
    ...


class ResearchOvercChecker(ResearchService):
    delay_check_interval: int = Field(60, validation_alias='DELAY_BETWEEN_TIME_CHECKING_SECONDS')


BASE_WORDS = ["завершено", "исследование завершено", "конец исследования", "окончено", "STOP"]


class ResearchWordStopper(BaseConfig):
    stop_words: List[str] = Field(
        default_factory=lambda: BASE_WORDS.copy(),
        alias='STOP_WORD_CHECKER_STOP_WORDS_LIST'
    )

    @field_validator("stop_words", mode='before')
    def split_str(cls, field_data):
        # Проверка, является ли значение строкой; если да, разделяем по запятой
        if isinstance(field_data, str):
            return field_data.split(',')
        return field_data


class ResearchPingator(BaseConfig):
    class ResearchPingDelayCalculator(BaseConfig):
        table: Dict[int, int] = Field(default={1: 1, 2: 6, 3: 24, 4: 48})


    ping_delay: ResearchPingDelayCalculator = Field(default_factory=ResearchPingDelayCalculator)

    max_pings_messages: int = Field(default=4,
                                    validation_alias='PINGATOR_MAX_PINGS_MESSAGES')
    ping_attempts_multiplier: int = Field(default=2,
                                          validation_alias='PINGATOR_PING_ATTEMPT_MULTIPLIER')
    ping_interval: int = Field(default=10,
                               validation_alias='PINGATOR_PING_INTERVAL_CHEKING')


research_pingator_settings = ResearchPingator()
research_overchecker_settings = ResearchOvercChecker()
research_wordstopper_settings = ResearchWordStopper()
