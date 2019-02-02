from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from .all_data import AllData


ChangedElementsType = Dict[str, List[Dict[str, Any]]]
DeletedElementsType = Dict[str, List[int]]


async def inform_changed_elements(all_data: AllData) -> None:
    from .websocket import Client

    changed_elements: ChangedElementsType = defaultdict(list)
    deleted_elements: DeletedElementsType = defaultdict(list)
    for collection, item_id in all_data.get_changed_elements():
        if item_id in all_data[collection]:
            changed_elements[collection].append(all_data[collection][item_id])
        else:
            deleted_elements[collection].append(item_id)

    await Client.send_to_all(
        {
            "type": "autoupdate",
            "changed": changed_elements,
            "deleted": deleted_elements,
            "all_data": False,
        }
    )
