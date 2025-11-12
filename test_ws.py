import asyncio
import websockets

async def test():
    async with websockets.connect("ws://localhost:6790/") as ws:
        await ws.send("hello")
        msg = await ws.recv()
        print(msg)

asyncio.run(test())
