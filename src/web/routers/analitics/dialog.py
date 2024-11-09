from fastapi import APIRouter
from fastapi import Depends

from src.database.postgres.engine.session import DatabaseSessionManager
from src.services.analitcs.metrics import BasicMetricCalculator
from src.web.dependencies.researcher.start import get_analytic_instruments
from src.web.dependencies.researcher.start import get_db_session
from src.web.utils.file import ZIPFileHandler
from src.web.utils.funcs import produce_analytic_data

router = APIRouter(prefix="/analytic/dialog", tags=["Analytic"])


# TODO Добавить сохранение файлов по пути


@router.post("/csv/zip", status_code=200)
async def get_csv_research_data(
        research_id: int,
        db_session: DatabaseSessionManager = Depends(get_db_session),
        analytic: dict = Depends(get_analytic_instruments),
):
    csv_analytic = analytic['csv'](
        research_id=research_id,
        session_manager=db_session,
        metric_calculator=BasicMetricCalculator,
    )
    data = await produce_analytic_data(csv_analytic)
    file_handler = ZIPFileHandler(data, "csv")
    return file_handler.create_response()


@router.post("/excel/zip", status_code=200)
async def get_excel_research_data(
        research_id: int,
        db_session: DatabaseSessionManager = Depends(get_db_session),
        analytic: dict = Depends(get_analytic_instruments),
):
    excel_analytic = analytic['excel'](
        research_id=research_id,
        session_manager=db_session,
        metric_calculator=BasicMetricCalculator,
    )
    data = await produce_analytic_data(excel_analytic)
    file_handler = ZIPFileHandler(data, "xlsx")
    return file_handler.create_response()
