from asyncio import sleep
import asyncio
from websockets import connect

command_queue = asyncio.Queue()


async def hello():
    print("start hello")
    async with connect("ws://localhost:8002") as websocket:
        while True:
            command = await command_queue.get()
            print(command)
            await websocket.send(command)


async def input_command():
    print("start command")
    while True:
        command = "send_msg"
        await command_queue.put(command)
        await asyncio.sleep(5)


async def main():
    task1 = asyncio.create_task(hello())
    task2 = asyncio.create_task(input_command())
    await asyncio.gather(task1, task2)


if __name__ == '__main__':
    asyncio.run(main())
