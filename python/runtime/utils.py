from __future__ import annotations


DEBUG = False


def debug(message: str) -> None:
    if DEBUG:
        print(message)
