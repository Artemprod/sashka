import asyncio
from fastapi_websocket_rpc import RpcMethodsBase, WebSocketRpcClient

async def run_client(uri):

    async with WebSocketRpcClient(uri, RpcMethodsBase()) as client:
        # call concat on the other side
        response = await client.other.send_message_me()
        # print result
        print(response.result)  # will print "hello world"

# run the client until it completes interaction with server
asyncio.get_event_loop().run_until_complete(
    run_client("ws://localhost:9001/ws")
)