"""
Container classes to handle all_data
"""

from __future__ import annotations

from collections import UserDict
from typing import Any, Dict, Generator, Tuple


ElementID = Tuple[str, int]
Element = Dict[str, Any]
CollectionType = Dict[int, Element]


class AllData(UserDict):
    """
    Container for the all_data dict.

    Like a normal dict but with the method get_changed_elements.
    """

    def __init__(self, initialdata: Dict[str, CollectionType]) -> None:
        for name, collection in initialdata.items():
            if isinstance(collection, dict):
                initialdata[name] = Collection(collection)  # type: ignore
        super().__init__(initialdata)

    def get_changed_elements(self) -> Generator[ElementID, None, None]:
        """
        Generator that returns all elements that have changed since the
        initialisation.
        """
        for name, collection in self.items():
            for item_id in collection.get_changed_elements():
                yield (name, item_id)

    def as_dict(self) -> Dict[str, CollectionType]:
        """
        Returns the data of the container as normal dict.
        """
        return {key: value.as_dict() for key, value in self.items()}


class Collection(UserDict):
    """
    Container for one collection inside all_data.

    Like a dict but with methods to add one element and get_changed_elements.
    """

    data: Dict[int, Element]
    name: str
    init_hashes: Dict[int, int]

    def __init__(self, initialdata: Dict[int, Element]) -> None:
        self.init_hashes = {}
        for item_id, element in initialdata.items():
            self.init_hashes[item_id] = hash(repr(element))
        super().__init__(initialdata)

    def add_element(self, element: Element) -> int:
        """
        Helper to add one element to the dict. Automaticly creates an id.
        """
        new_id = max(self) + 1
        element["id"] = new_id
        self[new_id] = element
        return new_id

    def get_changed_elements(self) -> Generator[int, None, None]:
        """
        Generator that returns all elements that have changed since the
        initialisation.
        """
        for item_id, element in self.items():
            if hash(repr(element)) != self.init_hashes.get(item_id):
                yield item_id

        yield from self.init_hashes.keys() - self.keys()

    def as_dict(self) -> Dict[int, Element]:
        """
        Returns the data of the collection as normal dict.
        """
        return self.data
