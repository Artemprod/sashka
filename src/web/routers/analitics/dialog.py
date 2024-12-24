from fastapi import APIRouter
from fastapi import Depends

from src.database.postgres.engine.session import DatabaseSessionManager
from src.services.analitcs.analitic import AnalyticExcel, AnalyticCSV, AnalyticJsonDialogs
from src.services.analitcs.metrics import BasicMetricCalculator
from src.web.dependencies.researcher.start import get_db_session
from src.web.utils.file import ZIPFileHandler
from src.web.utils.funcs import produce_analytic_data

router = APIRouter(prefix="/analytic/dialog", tags=["Analytic"])


# TODO Добавить сохранение файлов по пути


@router.post("/csv/zip", status_code=200)
async def get_csv_research_data(
        research_id: int,
        db_session: DatabaseSessionManager = Depends(get_db_session),

):

    csv_analytic = AnalyticCSV(
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

):
    excel_analytic = AnalyticExcel(
        research_id=research_id,
        session_manager=db_session,
        metric_calculator=BasicMetricCalculator,
    )
    data = await produce_analytic_data(excel_analytic)
    file_handler = ZIPFileHandler(data, "xlsx")
    return file_handler.create_response()

@router.get("/research/json", status_code=200)
async def get_dialogs_by_research(
        research_id: int,
        db_session: DatabaseSessionManager = Depends(get_db_session),

):
    json_analytic = AnalyticJsonDialogs(
        research_id=research_id,
        session_manager=db_session,
        metric_calculator=BasicMetricCalculator,
    )
    data = await json_analytic.provide_data()
    if data:
        return data

