import asyncio
import json
import random
import string
from collections import defaultdict
from contextlib import asynccontextmanager
from random import randint
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

import websockets


class Client:
    __slots__ = {
        "connection": Optional[websockets.WebSocketClientProtocol],
        "store": Dict[str, Dict[int, Dict[str, Any]]],
        "user_id": Optional[int],
        "current_requests": Dict[str, asyncio.Future],
    }

    def __init__(self) -> None:
        self.store: Dict[str, Dict[int, Dict[str, Any]]] = defaultdict(dict)
        self.current_requests: Dict[str, asyncio.Future] = {}
        self.connection = None
        self.user_id = None

    async def connect(self, address: str = "ws://localhost:8000") -> None:
        self.connection = await websockets.connect(address)
        asyncio.create_task(self.handle_recv())

    async def disconnect(self) -> None:
        if self.connection is not None:
            await self.connection.close()

    async def handle_recv(self) -> None:
        if self.connection is None:
            raise RuntimeError("Client not connected")
        try:
            async for raw_message in self.connection:
                message = json.loads(raw_message)
                message_type = message["type"]
                if message_type == "autoupdate":
                    await self.recv_autoupdate(message)
                elif message_type == "response":
                    await self.recv_response(message)
                else:
                    print(f"Unkown message {message_type}")

        except websockets.exceptions.ConnectionClosed:
            pass

    async def recv_autoupdate(self, message: Dict[str, Any]) -> None:
        if message["all_data"]:
            self.store = defaultdict(dict)

        for collection, elements in message["changed"].items():
            for element in elements:
                self.store[collection][int(element["id"])] = element

        for collection, element_ids in message["deleted"].items():
            for element_id in element_ids:
                if int(element_id) in self.store[collection]:
                    del self.store[collection][int(element_id)]

    async def recv_response(self, message: Dict[str, Any]) -> None:
        message_id = message["response-id"]
        future = self.current_requests[message_id]
        if "error" in message:
            # When the future is awaited, this takes a very long time. I don't know
            # why
            future.set_exception(ValueError(message["error"]))
        else:
            future.set_result(message["responses"])
        del self.current_requests[message_id]

    async def send(self, actions: List[dict]) -> asyncio.Future:
        """
        only sends actions.
        """
        if self.connection is None:
            raise RuntimeError("Client not connected")

        message_id = get_message_id()
        while message_id in self.current_requests:
            message_id = get_message_id()

        future = asyncio.get_running_loop().create_future()
        self.current_requests[message_id] = future
        await self.connection.send(json.dumps({"id": message_id, "actions": actions}))
        return future

    async def create_user(self, username: str) -> None:
        action: dict = {
            "action": "users/create_user",
            "payload": {"username": username},
        }
        response_waiter = await self.send([action])
        response = await response_waiter
        self.user_id = response[0]["id"]

    async def set_password(self, password: str) -> None:
        if self.user_id is None:
            raise RuntimeError("User for client is not connected.")
        action = {
            "action": "users/update_password",
            "payload": {"id": self.user_id, "password": password},
        }
        response_waiter = await self.send([action])
        await response_waiter


def get_message_id() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


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
