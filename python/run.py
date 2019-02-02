from __future__ import annotations

from importlib import import_module

from runtime.db import init_db
from runtime.websocket import serve


installed_apps = ["core", "users"]


def init() -> None:
    for app in installed_apps:
        import_module(f"apps.{app}")

    init_db()


init()
serve("localhost", 8000)
