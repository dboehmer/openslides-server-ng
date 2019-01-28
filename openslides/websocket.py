"""
Module for handeling the websocket connects.

Each client is an instance of the Consumer class.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Set

import websockets

from .actions import ActionData, ValidationError, handle_actions, prepare_actions
from .db import get_database


class Client:
    all_clients: Set["Client"] = set()

    def __init__(self, websocket: websockets.WebSocketServerProtocol) -> None:
        self.websocket = websocket

    def __enter__(self) -> "Client":
        self.all_clients.add(self)
        return self

    def __exit__(self, *args: Any) -> None:
        self.all_clients.remove(self)

    async def connected(self) -> None:
        """
        Called when the websocket is opened.
        """
        await self.send(
            {"changed": await get_database(), "deleted": {}, "all_data": True}
        )

    async def recv(self, message: List[ActionData]) -> None:
        """
        Our demo handels all incomming data as action. It has to have the format

        [
            {
                "action": "ACTION_NAME",
                "payload": {
                    "SOME": "DATA"
                }
            }
        ]
        """
        action_data = await prepare_actions(message)
        try:
            await handle_actions(action_data)
        except ValidationError as err:
            await self.send({"error": str(err)})

    async def send(self, message: Dict[str, Any]) -> None:
        """
        Sends data to the client. In this example, this is only autoupdate.
        """
        await self.websocket.send(json.dumps(message))

    @classmethod
    async def send_to_all(cls, message: Dict[str, Any]) -> None:
        """
        Sends data to all connected clients.
        """
        encoded = json.dumps(message)
        for client in cls.all_clients:
            await client.websocket.send(encoded)


async def handler(websocket: websockets.WebSocketServerProtocol, path: str) -> None:
    client = Client(websocket).__enter__()
    try:
        await client.connected()
        async for message in websocket:
            await client.recv(json.loads(message))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        client.__exit__()


def serve(host: str, port: int) -> None:
    start_server = websockets.serve(handler, host, port)
    asyncio.get_event_loop().run_until_complete(start_server)
    print(f"Started Server on {host}:{port}")
    asyncio.get_event_loop().run_forever()
