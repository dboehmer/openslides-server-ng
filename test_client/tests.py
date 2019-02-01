import asyncio
from contextlib import asynccontextmanager
from random import randint
from typing import AsyncGenerator, Callable, List

from client import Client


@asynccontextmanager
async def connect_clients(count: int) -> AsyncGenerator[List[Client], None]:
    clients: List[Client] = []
    try:
        clients = [Client() for _ in range(count)]
        await asyncio.gather(*(client.connect() for client in clients))

        yield clients

    finally:
        await asyncio.gather(*(client.disconnect() for client in clients))


async def create_users(
    clients: List[Client],
    username: Callable[[], str] = lambda: f"test-user-{randint(0, 1_000_000)}",
) -> None:
    await asyncio.gather(*(client.create_user(username()) for client in clients))


async def set_password(clients: List[Client], count: int = 10) -> None:
    coroutines = []
    for index in range(count):
        for client in clients:
            password = f"password{index}"
            coroutines.append(client.set_password(password))
    await asyncio.gather(*coroutines)
