import websockets
from typing import List, Dict, Any, Set
from collections import defaultdict
import json
import random
import string
import asyncio


class Client:
    __slots__ = {
        "connection": websockets.WebSocketClientProtocol,
        "store": Dict[str, Dict[int, Dict[str, Any]]],
        "username": str,
        "current_requests": Dict[str, asyncio.Future],
    }

    def __init__(self) -> None:
        self.store: Dict[str, Dict[int, Dict[str, Any]]] = defaultdict(dict)
        self.current_requests: Dict[str, asyncio.Future] = {}

    async def connect(self, address: str = "ws://localhost:8000") -> None:
        self.connection = await websockets.connect(address)

    async def disconnect(self) -> None:
        await self.connection.close()

    async def handle_recv(self) -> None:
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
        message_id = message["id"]
        future = self.current_requests[message_id]
        if "error" in message:
            # When the future is awaited, this takes a very long time. I don't know
            # why
            future.set_exception(ValueError(message["error"]))
        else:
            future.set_result(True)
        del self.current_requests[message_id]

    async def send(self, actions: List[dict]) -> asyncio.Future:
        """
        only sends actions.
        """
        message_id = get_message_id()
        while message_id in self.current_requests:
            message_id = get_message_id()

        future = asyncio.get_running_loop().create_future()
        self.current_requests[message_id] = future
        await self.connection.send(json.dumps({"id": message_id, "actions": actions}))
        return future

    async def create_user(self, username: str) -> None:
        action: dict = {"action": "users/create_user", "payload": {"username": username}}
        response = await self.send([action])
        await response
        self.username = username


def get_message_id() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))