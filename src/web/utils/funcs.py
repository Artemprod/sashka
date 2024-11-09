from typing import Union

from fastapi import HTTPException
from loguru import logger

from src.services.analitcs.models.analitic import AnalyticDataBufferDTO
from src.services.analitcs.models.analitic import AnalyticFileDTO


async def produce_analytic_data(analytic_instance) -> Union[AnalyticDataBufferDTO, AnalyticFileDTO]:
    try:
        return await analytic_instance.provide_data()
    except Exception as e:
        logger.error(f"Failed to retrieve research data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get research data: {str(e)}") from e
