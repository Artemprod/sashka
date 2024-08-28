from src.database.database_t import comon_database

from dataclasses import dataclass, field
from typing import List
from datetime import date


@dataclass
class UserResearch:
    owner: str
    client: str
    research_id: str  # Уникальный идентификатор исследования
    title: str  # Название исследования
    theme: str  # Тематика исследования
    status: int
    start_date: date  # Дата начала исследования
    end_date: date  # Дата окончания исследования
    user_ids: List[int]  # Список ID пользователей, участвующих в исследовании
    created_at: date = field(default_factory=date.today)  # Дата создания записи об исследовании
    updated_at: date = field(default_factory=date.today)

    def __str__(self):
        return f"status: {self.status}, users in progress {len(self.user_ids)}"


# Исследование 1
research1 = UserResearch(
    owner="Artem",
    client="",
    research_id="res001",
    title="Анализ использования Telegram-каналов",
    theme="Поведение пользователей в Telegram-каналах",
    status=0,
    start_date=date(2024, 7, 1),
    end_date=date(2024, 7, 31),
    user_ids=[101, 102, 103]
)
comon_database.save(research1.research_id, research1)

# Исследование 2
research2 = UserResearch(
    research_id="res002",
    owner="Artem",
    client="",
    title="Исследование предпочтений пользователей",
    theme="Пользовательские предпочтения в контенте",
    status=0,
    start_date=date(2024, 8, 1),
    end_date=date(2024, 8, 15),
    user_ids=[201, 202, 203]
)
comon_database.save(research2.research_id, research2)

# Исследование 3
research3 = UserResearch(
    owner="Artem",
    client="",
    research_id="res003",
    title="Анализ времени активности пользователей",
    theme="Временные паттерны активности",
    status=0,
    start_date=date(2024, 9, 1),
    end_date=date(2024, 9, 30),
    user_ids=[301, 302, 303]
)

research = UserResearch(
    owner="Artem",
    client="",
    research_id="res004",
    title="Анализ времени активности пользователей",
    theme="Временные паттерны активности",
    status=0,
    start_date=date(2024, 9, 1),
    end_date=date(2024, 9, 30),
    user_ids=[401, 402, 403]
)
comon_database.save(research3.research_id, research3)
comon_database.save(research.research_id, research)
comon_database.save('user_in_progress', [201, 202, 203, 302, 303])
d = {
    # Пример состояний пинга пользователей
    101: {"first": False, "second": False, "last": False},
    102: {"first": False, "second": False, "last": False},
    103: {"first": False, "second": False, "last": False},
    201: {"first": False, "second": False, "last": False},
    202: {"first": False, "second": False, "last": False},
    203: {"first": False, "second": False, "last": False},
    301: {"first": False, "second": False, "last": False},
    302: {"first": False, "second": False, "last": False},
    303: {"first": False, "second": False, "last": False},
    401: {"first": False, "second": False, "last": False},
    402: {"first": False, "second": False, "last": False},
    403: {"first": False, "second": False, "last": False},

}

comon_database.save('ping_status', d)
