"""
Creates a fake db and defines functions to read or write data.

Initialtes the database when the server starts.

Use get_all_data() and save_database() to handle the database.
"""


from __future__ import annotations

import asyncio
import json
from typing import Dict

from .all_data import AllData, CollectionType


DB_FILE = "all_data.json"
DATABASE: Dict[str, CollectionType] = {}
db_write_lock = asyncio.Lock()


def init_db() -> None:
    DATABASE.clear()
    with open(DB_FILE) as file:
        DATABASE.update(json.load(file))


async def get_all_data() -> AllData:
    """
    Returns an all_data dict for the current database.
    """
    return AllData(DATABASE)


async def get_database() -> Dict[str, CollectionType]:
    return DATABASE


async def save_database(all_data: AllData) -> None:
    """
    Saves an ALLData dict as new database.
    """
    DATABASE.clear()
    DATABASE.update(all_data.as_dict())
