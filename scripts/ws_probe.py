import asyncio
import websockets

async def main():
    uri = "ws://localhost:8000/ws/default"
    async with websockets.connect(uri) as ws:
        await ws.send("nearby cafes")
        for _ in range(3):
            msg = await asyncio.wait_for(ws.recv(), timeout=20)
            print(msg[:1000])
            print('---')

asyncio.run(main())
