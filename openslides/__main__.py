from __future__ import annotations

from importlib import import_module

from .db import init_db
from .websocket import serve


installed_apps = ["core"]


def init() -> None:
    for app in installed_apps:
        import_module(f".apps.{app}", package="openslides")

    init_db()


init()
serve("localhost", 8000)
