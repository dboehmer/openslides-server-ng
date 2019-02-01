from typing import Any, Dict

from runtime.actions import Action, ValidationError, all_data_var


class CreateUser(Action, name="users/create_user"):
    async def validate(self, payload: Dict[str, Any]) -> None:
        all_data = all_data_var.get()
        username = payload.get("username")
        if username is None:
            raise ValidationError("create_user action needs a username")
        if username in [user["username"] for user in all_data["users/user"].values()]:
            raise ValidationError(f"username `{username}` already exists")

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        all_data = all_data_var.get()
        item_id = all_data["users/user"].add_element(
            {
                "username": payload["username"],
                "created": payload["current_time"],
                "last_updated": payload["current_time"],
            }
        )
        return {"id": item_id}


class UpdatePassword(Action, name="users/update_password"):
    async def validate(self, payload: Dict[str, Any]) -> None:
        all_data = all_data_var.get()
        if "password" not in payload:
            raise ValidationError("update_password needs a password")
        if "id" not in payload:
            raise ValidationError("no password given")
        if payload["id"] not in all_data["users/user"]:
            raise ValidationError(f"User with id `{payload['id']}` does not exist.")

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        all_data = all_data_var.get()
        user = all_data["users/user"][payload["id"]]
        user["password"] = payload["password"]
        user["last_updated"] = payload["current_time"]
        return {}
