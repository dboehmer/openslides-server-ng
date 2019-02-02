from __future__ import annotations

import asyncio
from time import time

from client import connect_clients, create_users, set_password


CLIENT_COUNT = 100
starttime = time()


def log(message: str) -> None:
    print(f"{time() - starttime:.2f}: {message}")


async def test() -> None:
    log(f"connect {CLIENT_COUNT} clients.")
    async with connect_clients(CLIENT_COUNT) as clients:
        log("create users.")
        await create_users(clients)
        log("set passwords for each user 10 times.")
        await set_password(clients, count=10)
        log("all done. Disconnecting")


asyncio.run(test())
