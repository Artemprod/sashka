# import asyncio
# from datetime import datetime
#
# from sqlalchemy.orm import joinedload, selectinload
#
# from sqlalchemy import delete, insert, select, update, func, cast, Integer, and_
#
# from src.database.postgres.engine.session import DatabaseSessionManager
# from src.database.postgres.mock_models.enum_types import UserStatusEnum, ResearchStatusEnum
# from src.database.postgres.mock_models.many_to_many import UserResearch
# from src.database.postgres.mock_models.research import Research
#
# from src.database.postgres.mock_models.message import UserMessage, VoiceMessage, AssistantMessage
# from src.database.postgres.mock_models.research_owner import ResearchOwner
#
# from src.database.postgres.mock_models.status import UserStatus
#
# from src.database.postgres.mock_models.user import User
# from src.database.repository.base import BaseRepository
# from src.resrcher.mock_models import ResearchCashDTO
#
#
# class ResearchDataCashRepository(BaseRepository):
#     """Когда мне нужны просты CRUD операции я использую этот класс"""
#
#     async def get_cash_information(self, research_id: int):
#         async with self.db_session_manager.async_session_factory() as session:
#             async with session.begin():
#                 # Подзапрос для извлечения пользователей с определенным статусом
#                 user_subquery = (
#                     select(
#                         User.user_id,
#                         UserResearch.research_id
#                     )
#                     .join(User.status)
#                     .join(UserResearch, User.user_id == UserResearch.user_id)
#                     .where(
#                         UserStatusName.status_name == UserStatusEnum.IN_PROGRESS,
#                         UserResearch.research_id == research_id
#                     )
#                     .subquery()
#                 )
#
#                 # Основной запрос данных исследований с количеством пользователей и временем
#                 query = (
#                     select(
#                         Research.research_id,
#                         Research.research_status_id.label('research_status'),
#                         Research.start_date,
#                         Research.end_date,
#                         cast(func.count(user_subquery.c.user_id), Integer).label('user_in_progress'),
#                     )
#                     .outerjoin(user_subquery, user_subquery.c.research_id == Research.research_id)
#                     .where(Research.research_id == research_id)
#                     .group_by(
#                         Research.research_id,
#                         Research.research_status_id,
#                         Research.start_date,
#                         Research.end_date,
#                     )
#                 )
#
#                 # Выполнение запросов
#                 result = await session.execute(query)
#                 research_data = result.fetchone()
#
#                 if research_data:
#                     # Заполнение и возврат DTO
#                     research_dto = ResearchCashDTO(
#                         research_id=research_data.research_id,
#                         research_status=ResearchStatusEnum(research_data.research_status),
#                         user_in_progress=research_data.user_in_progress,
#                         start_date=research_data.start_date,
#                         end_date=research_data.end_date
#                     )
#                     return research_dto
#                 else:
#                     return None
