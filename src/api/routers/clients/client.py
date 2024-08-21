from fastapi import APIRouter
from starlette.requests import Request

clients_router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
)


@clients_router.post("/authorize")
async def start_session(request: Request):
    ...





