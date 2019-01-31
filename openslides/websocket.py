"""
Module for handeling the websocket connects.

Each client is an instance of the Consumer class.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Set

import websockets
from collections import defaultdict

from .actions import ActionData, ValidationError, handle_actions, prepare_actions
from .db import get_database
from .utils import debug


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
        all_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for collection, data in (await get_database()).items():
            for element in data.values():
                all_data[collection].append(element)

        await self.send(
            {"type": "autoupdate", "changed": all_data, "deleted": {}, "all_data": True}
        )

    async def recv(self, message: Dict[str, Any]) -> None:
        """
        Our demo handels all incomming data as action. It has to have the format

        {
            "id": "message_id",
            "actions": [
                {
                    "action": "ACTION_NAME",
                    "payload": {
                        "SOME": "DATA"
                    }
                }
            ]
        }
        """
        message_id = message["id"]
        action_data = await prepare_actions(message["actions"])
        try:
            await handle_actions(action_data)
        except ValidationError as err:
            await self.send({"type": "response", "error": str(err), "id": message_id})
        else:
            await self.send({"type": "response", "id": message_id})

    async def send(self, message: Dict[str, Any]) -> None:
        """
        Sends data to the client.
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
        debug(f"New connection, currently {len(Client.all_clients)} connected clients")
        await client.connected()
        async for message in websocket:
            await client.recv(json.loads(message))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        client.__exit__()
        debug(f"Lost connection, currently {len(Client.all_clients)} connected clients")


def serve(host: str, port: int) -> None:
    start_server = websockets.serve(handler, host, port)
    asyncio.get_event_loop().run_until_complete(start_server)
    print(f"Started Server on {host}:{port}")
    asyncio.get_event_loop().run_forever()
