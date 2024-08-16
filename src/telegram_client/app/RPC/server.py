import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi_websocket_rpc import RpcMethodsBase, WebsocketRPCEndpoint
from pyrogram import Client

from src.dispatcher.communicators.reggestry import ConsoleCommunicator
from src.telegram_client.app.app_manager import Manager
from src.telegram_client.app.model import ClientConfigDTO
from src.telegram_client.plugins.new_message_handler import echo


# Methods to expose to the clients
class ConcatServer(RpcMethodsBase):

    def __init__(self, client):
        super().__init__()
        self.client = client

    async def send_message_me(self):
        await self.client.send_message(chat_id=self.client.me.id, text="привет из RPC")
        return "отправлено сообщение"





client_configs = ClientConfigDTO(
    name="test",
    api_id="17349",
    api_hash="344583e45741c457fe1862106095a5eb",
    phone_number="9996601212",
    password='89671106966',
    test_mode=True,
)

client = Client(**client_configs.to_dict())
# Init the FAST-API app
app = FastAPI()
# Create an endpoint and load it with the methods to expose
endpoint = WebsocketRPCEndpoint(ConcatServer(client))
# add the endpoint to the app
endpoint.register_route(app, "/ws")


@app.on_event("startup")
async def startup_event():
    manager = Manager(client=client, coro=None, plug=dict(root=r"D:\projects\AIPO_V2\CUSTDEVER\src\telegram_client\plugins"))
    asyncio.create_task(manager.run(communicator=ConsoleCommunicator()))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9001)
