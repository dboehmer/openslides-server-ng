from ..actions import Action, ValidationError, all_data_var
from typing import Dict, Any


class CreateUser(Action, name="users/create_user"):
    async def validate(self, payload: Dict[str, Any]) -> None:
        all_data = all_data_var.get()
        username = payload.get("username")
        if username is None:
            raise ValidationError("create_user action needs a username")
        if username in [user["username"] for user in all_data["users/user"].values()]:
            raise ValidationError(f"username `{username}` already exists")

    async def execute(self, payload: Dict[str, Any]) -> None:
        all_data = all_data_var.get()
        all_data["users/user"].add_element({"username": payload["username"]})
