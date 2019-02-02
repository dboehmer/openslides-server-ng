"""
Creates a fake db and defines functions to read or write data.

Initialtes the database when the server starts.

Use get_all_data() and save_database() to handle the database.
"""


from __future__ import annotations

import asyncio
from typing import Any, Dict

import msgpack

from .all_data import AllData, CollectionType


DB_FILE = "all_data.msgpack"
DATABASE: Dict[str, CollectionType] = {}
db_write_lock = asyncio.Lock()


def init_db() -> None:
    """
    Loads the database from file and save it into memory.

    Use msgpack instead of json, because msgpack supports int-keys in dics.
    """
    DATABASE.clear()
    with open(DB_FILE, "rb") as file:
        database: Dict[str, Dict[int, Dict[str, Any]]] = {}
        for collection, data in msgpack.unpack(file, raw=False).items():
            database[collection] = {}
            for item_id, element in data.items():
                database[collection][item_id] = element

        DATABASE.update(database)


async def get_all_data() -> AllData:
    """
    Returns an all_data dict for the current database.
    """
    return AllData(await get_database())


async def get_database() -> Dict[str, CollectionType]:
    return dict_copy(DATABASE)


async def save_database(all_data: AllData) -> None:
    """
    Saves an ALLData dict as new database.
    """
    DATABASE.clear()
    DATABASE.update(all_data.as_dict())


def dict_copy(input_dict: dict) -> dict:
    """
    Creates a copy of a dict.
    """
    return msgpack.unpackb(msgpack.packb(input_dict), raw=True)
