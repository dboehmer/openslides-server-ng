from typing import Any, Dict

from runtime.actions import Action, ValidationError, all_data_var


def key_to_id(key: str) -> int:
    all_data = all_data_var.get()
    for config_id, config in all_data["core/config"].items():
        if config["key"] == key:
            return config_id
    raise ValidationError("Unknown config key `{key}`")


class SetConfig(Action, name="core/set_config"):
    async def validate(self, payload: Dict[str, Any]) -> None:
        if "key" not in payload:
            ValidationError("no key given")
        if "value" not in payload:
            ValidationError("no value given")
        all_data = all_data_var.get()

        if payload["key"] not in [
            config["key"] for config in all_data["core/config"].values()
        ]:
            ValidationError(f"unknown config variable {payload['key']}")

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        all_data = all_data_var.get()
        all_data["core/config"][key_to_id(payload["key"])]["value"] = payload["value"]
        return {}
