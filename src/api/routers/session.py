from environs import Env
from fastapi import APIRouter
from pyrogram import Client
from starlette.requests import Request


from src.dispatcher.dispatcher import Dispatcher
from src.telegram_client.app.app_manager import Manager

session_router = APIRouter(
    prefix="/session",
    tags=["Session"],
)

plugins = dict(root=r"D:\projects\AIPO_V2\CUSTDEVER\src\telegram_client\plugins")

@session_router.get("/start")
async def start_session(request: Request):
    env = Env()
    env.read_env('.env')
    session_path = r"D:\projects\AIPO_V2\CUSTDEVER\src\telegram_client\app\sessions\my_session.session"

    app = Client(name=session_path, api_id=env("API_ID"), api_hash=env("API_HASH"),
                 phone_number=env("PHONE_NUMBER"),
                 password=env("CLOUD_PASSWORD"),plugins=plugins)
    request.app.client = app

    manager = Manager(client=app)
    dispatcher = Dispatcher(manager=manager)
    await dispatcher.run_app('console')

@session_router.get("/check")
async def start_session(request: Request):
    app = request.app.client
    await app.send_message(chat_id=301213126, text="Ну че епт")
