import datetime
import random
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import List

from src_v0.database.database_t import comon_database


@dataclass
class Owner:
    name: str
    second_name: str
    phone_number: str
    tg_link: str
    language_code: str
    service_owner_id: int

    def to_dict(self):
        return asdict(self)


@dataclass
class UserResearch:
    owner: Owner
    service: str
    client: str
    assistant_id: int
    research_uuid: str  # Уникальный идентификатор исследования
    title: str  # Название исследования
    theme: str  # Тематика исследования
    status: int
    start_date: date  # Дата начала исследования
    end_date: date  # Дата окончания исследования
    user_ids: List[int]  # Список ID пользователей, участвующих в исследовании
    created_at: date = field(default_factory=date.today)  # Дата создания записи об исследовании
    updated_at: date = field(default_factory=date.today)  # Дата последнего обновления записи об исследовании

    def to_dict(self):
        return asdict(self)

    def __str__(self):
        return f"status: {self.status}, users in progress: {len(self.user_ids)}"


# Примеры объектов класса Owner
owner_data = Owner(
    name="Artem",
    second_name="Ivanov",
    phone_number="+1234567890",
    tg_link="@artem_ivanov",
    language_code="ru",
    service_owner_id=1234
)

# Исследование 1
research_im_1 = UserResearch(
    owner=owner_data,
    service='telegram',
    client="",
    research_uuid="res001",
    title="Анализ использования Telegram-каналов",
    theme="Поведение пользователей в Telegram-каналах",
    status=0,
    start_date=datetime.datetime.now(),
    end_date = datetime.datetime.now() + datetime.timedelta(minutes=3),
    user_ids=[random.randint(9000000,999999000) for i in range(4)],
    assistant_id=1
)
comon_database.save(research_im_1.research_uuid, research_im_1)

# Исследование 2
research2 = UserResearch(
    owner=owner_data,
    service='telegram',
    client="",
    research_uuid="res002",
    title="Исследование предпочтений пользователей",
    theme="Пользовательские предпочтения в контенте",
    status=0,
    start_date=date(2024, 8, 1),
    end_date=date(2024, 8, 15),
    user_ids=[201, 202, 203],
    assistant_id=1
)
comon_database.save(research2.research_uuid, research2)

# Исследование 3
research3 = UserResearch(
    owner=owner_data,
    service='telegram',
    client="",
    research_uuid="res003",
    title="Анализ времени активности пользователей",
    theme="Временные паттерны активности",
    status=0,
    start_date=date(2024, 9, 1),
    end_date=date(2024, 9, 30),
    user_ids=[301, 302, 303],
    assistant_id=1
)
comon_database.save(research3.research_uuid, research3)

# Дополнительное исследование (research4)
research4 = UserResearch(
    owner=owner_data,
    service='telegram',
    client="",
    research_uuid="res004",
    title="Анализ времени активности пользователей",
    theme="Временные паттерны активности",
    status=0,
    start_date=date(2024, 9, 1),
    end_date=date(2024, 9, 30),
    user_ids=[401, 402, 403],
    assistant_id=1,
)
comon_database.save(research4.research_uuid, research4)
comon_database.save(research3.research_uuid, research3)
# comon_database.save(research.research_id, research)
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
