from fastapi import APIRouter, HTTPException
from fastapi import Depends
from starlette.responses import JSONResponse

from configs.cloud_storage import s3_selectel_settings
from src.database.postgres.engine.session import DatabaseSessionManager
from src.services.analitcs.analitic import AnalyticExcel, AnalyticCSV, AnalyticJsonDialogs
from src.services.analitcs.metrics import BasicMetricCalculator
from src.services.cloud_storage.s3.clietn import S3Client
from src.web.dependencies.researcher.start import get_db_session, get_s3_report_storage
from src.web.models.analitics import AnalyticDTO
from src.web.utils.file import ZIPFileHandler
from src.web.utils.funcs import produce_analytic_data

router = APIRouter(prefix="/analytic/dialog", tags=["Analytic"])


# TODO Добавить сохранение файлов по пути


@router.post("/csv/zip", status_code=200)
async def get_csv_research_data(
    request_dto: AnalyticDTO,
    db_session: DatabaseSessionManager = Depends(get_db_session),
    s3_client: S3Client = Depends(get_s3_report_storage),
):
    csv_analytic = AnalyticCSV(
        research_status=request_dto.research_status,
        research_id=request_dto.research_id,
        session_manager=db_session,
        metric_calculator=BasicMetricCalculator,
    )
    data = await produce_analytic_data(csv_analytic)
    file_handler = ZIPFileHandler(s3_client, data, "csv")
    object_name = await file_handler.save_and_upload_file()
    # Генерация предподписанной ссылки для скачивания файла
    download_url = await s3_client.generate_presigned_url(object_name)
    if download_url:
        return JSONResponse(content={"download_url": download_url})
    else:
        return HTTPException(status_code=204, detail=f"No content")


@router.post("/excel/zip", status_code=200)
async def get_excel_research_data(
    request_dto: AnalyticDTO,
    db_session: DatabaseSessionManager = Depends(get_db_session),
    s3_client: S3Client = Depends(get_s3_report_storage),
):
    excel_analytic = AnalyticExcel(
        research_status=request_dto.research_status,
        research_id=request_dto.research_id,
        session_manager=db_session,
        metric_calculator=BasicMetricCalculator,
    )
    data = await produce_analytic_data(excel_analytic)

    file_handler = ZIPFileHandler(s3_client, data, "xlsx")
    object_name = await file_handler.save_and_upload_file()
    # Генерация предподписанной ссылки для скачивания файла
    download_url = await s3_client.generate_presigned_url(object_name)

    if download_url:
        return JSONResponse(content={"download_url": download_url})
    else:
        return HTTPException(status_code=204, detail=f"No content")


@router.post("/research/json", status_code=200)
async def get_dialogs_by_research(
    request_dto: AnalyticDTO,
    db_session: DatabaseSessionManager = Depends(get_db_session),
):
    json_analytic = AnalyticJsonDialogs(
        research_status=request_dto.research_status,
        research_id=request_dto.research_id,
        session_manager=db_session,
        metric_calculator=BasicMetricCalculator,
    )
    data = await json_analytic.provide_data()
    if data:
        return data
