import asyncio
from fastapi_websocket_rpc import RpcMethodsBase, WebSocketRpcClient

async def send_message(client:WebSocketRpcClient):

    async with client:
        # call concat on the other side
        response = await client.other.send_message_me()
        # print result
        print(response.result)  # will print "hello world"

# run the client until it completes interaction with server
async def main():
    client = WebSocketRpcClient("ws://localhost:9001/ws", RpcMethodsBase())
    await send_message(client)
    await send_message(client)
    await send_message(client)


asyncio.run(main())