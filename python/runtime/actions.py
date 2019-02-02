from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Type

from mypy_extensions import TypedDict

from contextvars import ContextVar

from .all_data import AllData
from .autoupdate import inform_changed_elements
from .db import db_write_lock, get_all_data, save_database
from .utils import debug


all_data_var: ContextVar[AllData] = ContextVar("all_data")


class ValidationError(Exception):
    """
    Exception, if the payload of an action is wrong.
    """


class Action:
    all_actions: Dict[str, Type["Action"]] = {}
    name: str

    def __init_subclass__(cls, name: str, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)  # type: ignore
        cls.name = name
        cls.all_actions[name] = cls

    @classmethod
    def get_action(cls, name: str) -> "Action":
        try:
            return cls.all_actions[name]()
        except KeyError:
            raise ValidationError(f"Unknown action with name `{name}`")

    async def validate(self, payload: Dict[str, Any]) -> None:
        """
        The implementation of an action should validate the payload.

        This is called before the database lock. So do not edit anything here.
        """

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Method to manipulate the data.
        """


class ActionData(TypedDict):
    action: str
    payload: Dict[str, Any]


async def prepare_actions(
    actions: List[ActionData],
    # request_user: str,
    now: Callable[[], datetime] = None,
) -> List[ActionData]:
    """
    Adds the current time and the request user to the payload of any action.
    """
    if now is None:
        now = datetime.utcnow

    current_time = now().timestamp()

    def add_data(action: ActionData) -> ActionData:
        # action["payload"]["request_user"] = request_user
        action["payload"]["current_time"] = current_time
        return action

    return list(map(add_data, actions))


async def handle_actions(actions_data: List[ActionData]) -> List[Dict[str, Any]]:
    all_data = await get_all_data()
    all_data_var.set(all_data)
    return_values: List[Dict[str, Any]] = []

    async with db_write_lock:
        for action_data in actions_data:
            debug(
                f"handle action {action_data['action']} with payload {action_data['payload']}"
            )
            action = Action.get_action(action_data["action"])
            await action.validate(action_data["payload"])
            return_values.append(await action.execute(action_data["payload"]))

        await save_database(all_data)

    await inform_changed_elements(all_data)
    return return_values
