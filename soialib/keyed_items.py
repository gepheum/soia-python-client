import abc
from typing import Generic, Optional, TypeVar


Item = TypeVar("Item")
Key = TypeVar("Key")


class KeyedItems(Generic[Item, Key], tuple[Item, ...], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def find(self, key: Key) -> Optional[Item]: ...

    @abc.abstractmethod
    def find_or_default(self, key: Key) -> Item: ...
