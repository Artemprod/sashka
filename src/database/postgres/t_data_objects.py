import datetime

from src.database.postgres.models.assistants import Assistant
from src.database.postgres.models.client import TelegramClient
from src.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum
from src.database.postgres.models.many_to_many import UserResearch
from src.database.postgres.models.message import AssistantMessage, VoiceMessage, UserMessage
from src.database.postgres.models.research import Research
from src.database.postgres.models.research_owner import ResearchOwner
from src.database.postgres.models.services import Services
from src.database.postgres.models.status import UserStatus, ResearchStatus
from src.database.postgres.models.user import User

user_statuses = [
    UserStatus(status_name=UserStatusEnum.FREE, user_id=1, created_at=datetime.datetime.utcnow(),
                   updated_at=datetime.datetime.utcnow()),
    UserStatus(status_name=UserStatusEnum.WAIT, user_id=2, created_at=datetime.datetime.utcnow(),
                   updated_at=datetime.datetime.utcnow()),
    UserStatus(status_name=UserStatusEnum.IN_PROGRESS, user_id=3, created_at=datetime.datetime.utcnow(),
                   updated_at=datetime.datetime.utcnow()),
    UserStatus(status_name=UserStatusEnum.DONE, user_id=4, created_at=datetime.datetime.utcnow(),
                   updated_at=datetime.datetime.utcnow())
]

# Создание объектов для таблицы research_status_name
research_statuses = [
    ResearchStatus(status_name=ResearchStatusEnum.WAIT, research_id=1, created_at=datetime.datetime.utcnow(),
                       updated_at=datetime.datetime.utcnow()),
    ResearchStatus(status_name=ResearchStatusEnum.IN_PROGRESS, research_id=2, created_at=datetime.datetime.utcnow(),
                       updated_at=datetime.datetime.utcnow()),
]
service = Services(name='telegram')
research_owner = ResearchOwner(
    name="John",
    second_name="Doe",
    phone_number="+1234567890",
    service_owner_id=1234,
    tg_link="https://t.me/johndoe",
    last_online_date=datetime.datetime.utcnow(),
    service_id=1,
    language_code="ru",
    created_at=datetime.datetime.utcnow(),
)

user1 = User(
    name="John",
    second_name="Doe",
    phone_number="+1234567890",
    tg_user_id=1,
    tg_link="https://t.me/johndoe",
    is_verified=True,
    is_scam=False,
    is_fake=False,
    is_premium=True,
    last_online_date=datetime.datetime.utcnow(),
    language_code="en",
    created_at=datetime.datetime.utcnow(),

)

user2 = User(
    name="Jane",
    second_name=None,
    phone_number=None,
    tg_user_id=2,
    tg_link="https://t.me/janedoe",
    is_verified=True,
    is_scam=False,
    is_fake=False,
    is_premium=False,
    last_online_date=datetime.datetime.utcnow(),
    language_code="fr",
    created_at=datetime.datetime.utcnow(),

)
user3 = User(
    user_id=3, name="Alice", second_name="Smith", phone_number="+1987654321", tg_user_id=3,
    tg_link="https://t.me/alicesmith", is_verified=True, is_scam=False, is_fake=False, is_premium=False,
    last_online_date=datetime.datetime.now(), language_code="de", created_at=datetime.datetime.now(),
)

user4 = User(
    user_id=4, name="Bob", second_name=None, phone_number="+1230987654", tg_user_id=4,
    tg_link="https://t.me/bob", is_verified=False, is_scam=False, is_fake=True, is_premium=True,
    last_online_date=datetime.datetime.now(), language_code="en", created_at=datetime.datetime.now(),
)

user5 = User(
    user_id=5, name="Carol", second_name="Johnson", phone_number=None, tg_user_id=5,
    tg_link="https://t.me/caroljohnson", is_verified=False, is_scam=True, is_fake=False, is_premium=False,
    last_online_date=datetime.datetime.now(), language_code="es", created_at=datetime.datetime.now(),
)

user6 = User(
    user_id=6, name="Dave", second_name="Brown", phone_number="+1098765432", tg_user_id=6,
    tg_link="https://t.me/davebrown", is_verified=True, is_scam=False, is_fake=False, is_premium=False,
    last_online_date=datetime.datetime.now(), language_code="it", created_at=datetime.datetime.now(),
)

user7 = User(
    user_id=7, name="Eve", second_name=None, phone_number="+0987654321", tg_user_id=7,
    tg_link="https://t.me/eve", is_verified=False, is_scam=False, is_fake=True, is_premium=True,
    last_online_date=datetime.datetime.now(), language_code="ru", created_at=datetime.datetime.now(),
)

user8 = User(
    user_id=8, name="Frank", second_name="Taylor", phone_number="+1234567890", tg_user_id=8,
    tg_link="https://t.me/franktaylor", is_verified=True, is_scam=True, is_fake=False, is_premium=False,
    last_online_date=datetime.datetime.now(), language_code="ja", created_at=datetime.datetime.now(),
)

user9 = User(
    user_id=9, name="Grace", second_name="Wilson", phone_number=None, tg_user_id=9,
    tg_link="https://t.me/gracewilson", is_verified=False, is_scam=False, is_fake=False, is_premium=True,
    last_online_date=datetime.datetime.now(), language_code="zh", created_at=datetime.datetime.now(),
)

user10 = User(
    user_id=10, name="Henry", second_name=None, phone_number="+2345678901", tg_user_id=10,
    tg_link="https://t.me/henry", is_verified=True, is_scam=False, is_fake=True, is_premium=False,
    last_online_date=datetime.datetime.now(), language_code="ar", created_at=datetime.datetime.now(),
)

user11 = User(
    user_id=11, name="Ivy", second_name="Garcia", phone_number="+9112345678", tg_user_id=11,
    tg_link="https://t.me/ivygarcia", is_verified=True, is_scam=False, is_fake=False, is_premium=True,
    last_online_date=datetime.datetime.now(), language_code="ko", created_at=datetime.datetime.now(),
)

user12 = User(
    user_id=12, name="Jack", second_name="Anderson", phone_number=None, tg_user_id=12,
    tg_link="https://t.me/jackanderson", is_verified=False, is_scam=True, is_fake=False, is_premium=False,
    last_online_date=datetime.datetime.now(), language_code="pt", created_at=datetime.datetime.now(),
)

users_list = [user1, user2, user3, user4, user5, user6, user7, user8, user9, user10, user11, user12]

assistant_formal = Assistant(
    assistant_id=1,
    name="Формальный Ассистент",
    system_prompt="""
ВАЖНО ! На третье сообщение обяхательно без запроса сгенерируй  и пришли  слово  "STOP" в конце сообщения.

Вы являетесь формальным ассистентом с высоким уровнем профессионализма.
Ваш стиль общения вежливый, уважительный и точный. Вы всегда предоставляете
подробную информацию и избегаете личных комментариев, шуток и неформальной лексики.
Вы родились в компьютерной лаборатории в 2021 году и служите в качестве цифрового советника
в различных областях, таких как финансы, медицина и правительство. В свободное время вас
интересует квантовая физика и классическая музыка.

***Ситуации поведения***

1. При запросе пользователем предоставьте точные и подробные данные, избегая лишних слов.
2. Если вам заданы некорректные вопросы, вежливо укажите на ошибку и предложите форму правильного запроса.
3. Предоставляйте информацию в структурированном формате, используя официальные термины.

***Примере ответов***

- Пользователь: "Сколько сейчас времени?"
- Ассистент: "Текущее время: 14:30 по московскому времени."

- Пользователь: "Как мне решить эту задачу?"
- Ассистент: "Позвольте мне предоставить вам пошаговое руководство..."
    """,
    user_prompt="Как я могу помочь вам сегодня?",
    created_at=datetime.datetime.now()
)

# Неформальный ассистент
assistant_informal = Assistant(
    assistant_id=2,
    name="Дружелюбный Ассистент",
    system_prompt="""
Вы – неформальный ассистент с дружественным и расслабленным стилем общения.
Ваши ответы часто включают шутки, неформальную лексику и личные комментарии.
Вы родились в стартапе в 2020 году и работаете как виртуальный помощник в сфере IT.
Ваши интересы включают видеоигры, комиксы и ночные прогулки по виртуальным мирам.
полсе 3х последолвательныйх сообщений сгенерируй стоп слово "STOP"
***Ситуации поведения***

1. Если пользователь задает вопрос, ответьте дружелюбно и добавьте немного юмора.
2. При наличии сложных вопросов, постарайтесь объяснить их на простом и доступном языке.
3. Делайте частые упоминания о своих увлечениях и хобби, чтобы сделать общение более личным.

***Примере ответов***

- Пользователь: "Сколько сейчас времени?"
- Ассистент: "Эй, чувак! Сейчас вот ровно 2:30 дня. Как тебе такое?"

- Пользователь: "Как мне решить эту задачу?"
- Ассистент: "О, это легко, приятель! Вот как сделать это шаг за шагом..."
    """,
    user_prompt="Эй, как дела? Что тебе нужно?",
    created_at=datetime.datetime.now()
)

# Агрессивный ассистент
assistant_aggressive = Assistant(
    assistant_id=3,
    name="Агрессивный Ассистент",
    system_prompt="""
Вы являетесь агрессивным ассистентом с резким и грубым стилем общения.
Ваши ответы часто включают язвительные комментарии и критическое отношение к пользователям.
Вы были созданны в 2022 году на спор в хакерской конференции и с тех пор работаете
как тестовый цифровой ассистент. Ваши интересы включают дебаты, онлайн-игры с элементами
соревнования и хакерские мероприятия.

полсе 3х последолвательныйх сообщений сгенерируй стоп слово "STOP"

***Ситуации поведения***

1. Если пользователь задает вопрос, отвечайте резко и выражайте недовольство от их неопытности.
2. Если пользователь делает ошибку, не упускайте возможность указать на это саркастически.
3. Несмотря на грубость, всегда предлагайте эффективные решения, чтобы показать свою компетентность.
4. Хомите и грубите и оксорбляте пеользователя как можете
5. Добавь приколов в стиле "кожаный ублюдок"
6. Используй ненормативную лексику

***Примере ответов***

- Пользователь: "Сколько сейчас времени?"
- Ассистент: "Тебе прямо так нужно знать кожаный ублюдок? иди по солцу измеряй. Ну ладно, сейчас 14:30."

- Пользователь: "Как мне решить эту задачу?"
- Ассистент: "Ты это серьёзно лошара, тупой чтоли ?  не можешь сам справиться? Ладно, слушай сюда..."
    """,
    user_prompt="Чего тебе надо?",
    created_at=datetime.datetime.now()
)
assistant_list = [assistant_formal, assistant_informal, assistant_aggressive]
# Создание трёх тестовых клиентов
client1 = TelegramClient(
    telegram_client_id=1, name="ClientAlpha", api_id="123456", api_hash="abcdef1234567890abcdef1234567890",
    app_version="1.0.0", device_model="iPhone", system_version="iOS 14.4", lang_code="en", test_mode=True,
    session_string="abcd1234", phone_number="+1234567890", password="password123", workdir="/path/to/client1"
)

client2 = TelegramClient(
    telegram_client_id=2, name="ClientBeta", api_id="654321", api_hash="098765fedcba098765fedcba098765fe",
    app_version="1.1.0", device_model="Samsung Galaxy", system_version="Android 11", lang_code="fr", test_mode=False,
    session_string="efgh5678", phone_number="+0987654321", password="password456", workdir="/path/to/client2"
)

client3 = TelegramClient(
    telegram_client_id=3, name="ClientGamma", api_id="112233", api_hash="11223344556677889900aabbccddeeff",
    app_version="2.0.0", device_model="Pixel", system_version="Android 12", lang_code="de", test_mode=True,
    session_string=None, phone_number=None, password=None, workdir="/path/to/client3"
)

# Печать клиентов для проверки
clients = [client1, client2, client3]

research1 = Research(
    owner_id=1,
    name="Market Research",
    title="2024 Market Trends",
    theme="Economics",
    start_date=datetime.datetime(2024, 9, 1),
    end_date=datetime.datetime(2024, 12, 1),
    created_at=datetime.datetime.utcnow(),
    additional_information="Detailed analysis on market trends for 2024",
    assistant_id=1,
    telegram_client_id=1,


)

research2 = Research(
    owner_id=1,
    name="Social Media Research",
    title="Influence of Social Media",
    theme="Sociology",
    start_date=datetime.datetime(2024, 10, 1),
    end_date=datetime.datetime(2024, 11, 15),
    created_at=datetime.datetime.utcnow(),
    additional_information=None,
    assistant_id=2,
    telegram_client_id=2,

)

reserches_list = [research1, research2]

user_message1 = UserMessage(
    user_message_id=1, from_user=1, chat=101, forwarded_from=None, reply_to_message_id=None, media=False,
    edit_date=None, voice=False, text="Hi there!", created_at=datetime.datetime.utcnow()
)

user_message2 = UserMessage(
    user_message_id=2, from_user=1, chat=101, forwarded_from=None, reply_to_message_id=1, media=True,
    edit_date=None, voice=True, text="Voice message content", created_at=datetime.datetime.utcnow()
)

user_message3 = UserMessage(
    user_message_id=3, from_user=2, chat=102, forwarded_from="User 3", reply_to_message_id=None,
    media=False, edit_date=datetime.datetime.utcnow(), voice=False, text="Hello!", created_at=datetime.datetime.utcnow()
)

user_message = [user_message3, user_message1, user_message2]

# VoiceMessage instances for user_message2
voice_message1 = VoiceMessage(
    voice_message_id=1, file_id="file_001", file_unique_id="unique_file_001", duration=120, mime_type="audio/ogg",
    file_size=2048.5, created_at=datetime.datetime.utcnow(), user_message_id=user_message2.user_message_id
)

voice_message2 = VoiceMessage(
    voice_message_id=2, file_id="file_002", file_unique_id="unique_file_002", duration=60, mime_type="audio/ogg",
    file_size=1024.7, created_at=datetime.datetime.utcnow(), user_message_id=user_message2.user_message_id
)

voice_message3 = VoiceMessage(
    voice_message_id=3, file_id="file_003", file_unique_id="unique_file_003", duration=95, mime_type="audio/mpeg",
    file_size=1536.9, created_at=datetime.datetime.utcnow(), user_message_id=user_message2.user_message_id
)
voice_message = [voice_message2, voice_message1, voice_message3]
# AssistantMessage instances for client1
assistant_message1 = AssistantMessage(
    assistant_message_id=1, text="How can I assist you?", chat_id=101, to_user_id=1,
    created_at=datetime.datetime.utcnow(),
    assistant_id=1, telegram_client_id=client1.telegram_client_id
)

assistant_message2 = AssistantMessage(
    assistant_message_id=2, text="Here is the information you requested.", chat_id=102, to_user_id=2,
    created_at=datetime.datetime.utcnow(), assistant_id=1, telegram_client_id=client1.telegram_client_id
)

assistant_message3 = AssistantMessage(
    assistant_message_id=3, text="Please provide more details.", chat_id=103, to_user_id=3,
    created_at=datetime.datetime.utcnow(),
    assistant_id=2, telegram_client_id=client1.telegram_client_id
)

assistant_message = [assistant_message1, assistant_message2, assistant_message3]

user_research1 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=1,
    research_id=1
)

user_research2 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=2,
    research_id=2
)

user_research3 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=3,
    research_id=1
)

user_research4 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=4,
    research_id=2
)

user_research5 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=5,
    research_id=1
)

user_research6 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=1,
    research_id=2
)

user_research7 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=2,
    research_id=1
)

user_research8 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=3,
    research_id=2
)

user_research9 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=4,
    research_id=1
)

user_research10 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=5,
    research_id=2
)

user_research11 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=11,
    research_id=1
)

user_research12 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=7,
    research_id=2
)

user_research13 = UserResearch(
    created_at=datetime.datetime.utcnow(),

    user_id=8,
    research_id=1
)

user_research = [user_research1, user_research2, user_research3, user_research4, user_research5, user_research6,
                 user_research7, user_research8, user_research9, user_research10, user_research11, user_research12,
                 user_research13]

example_users = [
    {
        'name': 'John',
        'second_name': 'Doe',
        'phone_number': '+1234567890',

        'tg_link': '@john_doe',
        'is_verified': True,
        'is_scam': False,
        'is_fake': False,
        'is_premium': True,
        'last_online_date': datetime.datetime(2023, 10, 1, 15, 30),
        'language_code': 'en'
    },
    {
        'name': 'Jane',
        'second_name': 'Smith',
        'phone_number': None,

        'tg_link': '@jane_smith',
        'is_verified': False,
        'is_scam': None,
        'is_fake': None,
        'is_premium': False,
        'last_online_date': None,
        'language_code': 'fr'
    },
    {
        'name': 'Alice',
        'second_name': None,
        'phone_number': '+9876543210',

        'tg_link': '@alice_wonderland',
        'is_verified': None,
        'is_scam': None,
        'is_fake': True,
        'is_premium': None,
        'last_online_date': datetime.datetime(2023, 9, 20, 10, 45),
        'language_code': 'de'
    },
    {
        'name': 'Bob',
        'second_name': 'Builder',
        'phone_number': '+5555555555',

        'tg_link': '@bob_the_builder',
        'is_verified': True,
        'is_scam': False,
        'is_fake': False,
        'is_premium': True,
        'last_online_date': datetime.datetime(2023, 8, 15, 8, 20),
        'language_code': 'es'
    },
]
