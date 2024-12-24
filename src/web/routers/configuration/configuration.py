from fastapi import APIRouter, Depends
from fastapi import HTTPException
from loguru import logger

from src.database.repository.storage import RepoStorage
from src.web.dependencies.researcher.start import get_repository
from src.web.models.configuration import ConfigurationCreateSchema, ConfigurationSchema

router = APIRouter(prefix="/configuration", tags=["Configuration"])


@router.put("")
async def create_or_update_configuration(
        configuration: ConfigurationCreateSchema,
        repository: RepoStorage = Depends(get_repository),
) -> ConfigurationSchema:
    """
    Этот эндпоинт принимает данные конфигурации и либо создает новую запись в базе данных,
    либо обновляет существующую, если она уже существует.
    """
    try:
        return await repository.configuration_repo.create_or_update(values=configuration)

    except Exception as e:
        logger.error(f"Failed to update configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}") from e


@router.get("")
async def get_configuration(
        repository: RepoStorage = Depends(get_repository)
) -> ConfigurationSchema:
    """
    Этот эндпоинт возвращает единственную запись конфигурации из базы данных.
    Если конфигурация не найдена, будет выброшено исключение.
    """

    return await repository.configuration_repo.get()
