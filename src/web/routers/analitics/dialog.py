from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from src.database.postgres.engine.session import DatabaseSessionManager
from src.services.analitcs.diolog import ResearchDialogs
from src.web.dependencies.researcher.start import get_research_manager, get_publisher, get_db_session

router = APIRouter(prefix="/analytic/dialog", tags=["Telegram"])





@router.post("/get_dialog",status_code=200)
async def start_research(research_id:int, db_session: DatabaseSessionManager = Depends(get_db_session)):
    """Запускает новый процесс исследования."""
    research_dialogs: ResearchDialogs = ResearchDialogs(session_manager=db_session, research_id=research_id)
    try:
        dialogs = await research_dialogs.get_dialogs()
        return dialogs
    except Exception as e:
        logger.error(f"Failed : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start research: {str(e)}")
