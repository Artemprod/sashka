from environs import Env
from fastapi import APIRouter
from pyrogram import Client
from starlette.requests import Request


from src.dispatcher.dispatcher import Dispatcher
from src.telegram_client.app.app_manager import Manager
from websockets.sync.client import connect
session_router = APIRouter(
    prefix="/session",
    tags=["Session"],
)


@session_router.get("/start")
async def start_session(request: Request):
    env = Env()
    env.read_env('.env')
    session_path = r"D:\projects\AIPO_V2\CUSTDEVER\src\telegram_client\app\sessions\my_session.session"



@session_router.get("/check")
async def start_session():
    with connect("ws://localhost:8002") as websocket:
        websocket.send("send_msg")
