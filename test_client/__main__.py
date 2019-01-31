from .client import Client
import asyncio
from random import randint
import websockets


async def test1() -> None:
    client = Client()
    await client.connect()
    asyncio.create_task(client.handle_recv())
    await client.create_user(f"test-user-{randint(0, 1_000_000)}")
    await client.disconnect()


asyncio.run(test1())
