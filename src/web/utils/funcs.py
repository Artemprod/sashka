from collections import Counter
from itertools import count
from typing import Union, List

from fastapi import HTTPException
from loguru import logger

from src.schemas.information.start_research import UserInfo, NameInfo
from src.schemas.service.research import ResearchDTOPost
from src.schemas.service.user import UserDTO
from src.services.analitcs.models.analitic import AnalyticDataBufferDTO
from src.services.analitcs.models.analitic import AnalyticFileDTO
from src.utils.wrappers import async_wrap


async def produce_analytic_data(analytic_instance) -> Union[AnalyticDataBufferDTO, AnalyticFileDTO]:
    try:
        return await analytic_instance.provide_data()
    except Exception as e:
        logger.error(f"Failed to retrieve research data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get research data: {str(e)}") from e

@async_wrap
def count_users_in_research(users_dto:[List[UserDTO]],research:ResearchDTOPost)->UserInfo:
    """
    Функция которая принимает имена пользователей котрые были лобвленеыф в иследование
    и именга пользователоей по которым была собрана ифнформация то есть те у которых есть имя
    и возвращет статситику того сколько пользователей бюыли добалены и скольок осталовьс не добавленых
    """
    #Реши при помощи множества
    # A = set()
    # B = set()
    # C = A/B - есть А без B

    initial_amount_of_users = set(user_name for user_name in research.examinees_user_names)
    added_users = set(user.username for user in users_dto)
    wrong_names = initial_amount_of_users - added_users

    return UserInfo(
        correct_names=NameInfo(
            names=added_users,
            total=Counter(added_users).total(),
    ),
         wrong_names=NameInfo(
            names=wrong_names,
            total=Counter(wrong_names).total(),
             )
    )
