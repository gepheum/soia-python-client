from collections.abc import Callable
from dataclasses import FrozenInstanceError
from typing import Generic, Optional
from weakref import WeakValueDictionary

from soialib import spec
from soialib.impl.function_maker import Any, Expr, ExprLike, Line, make_function
from soialib.impl.type_adapter import TypeAdapter
from soialib.keyed_items import Item, Key, KeyedItems


def get_array_adapter(
    item_adapter: TypeAdapter,
    key_attributes: tuple[str, ...],
) -> TypeAdapter:
    if key_attributes:
        default_expr = item_adapter.default_expr()
        listuple_class = _new_keyed_items_class(key_attributes, default_expr)
    else:
        listuple_class = _new_listuple_class()
    array_adapter = _ArrayAdapter(item_adapter, listuple_class)
    return _item_to_array_adapter.setdefault(
        (item_adapter, key_attributes), array_adapter
    )


class _ArrayAdapter(TypeAdapter):
    __slots__ = (
        "item_adapter",
        "listuple_class",
        "empty_listuple",
    )

    item_adapter: TypeAdapter
    listuple_class: type
    empty_listuple: tuple[()]

    def __init__(
        self,
        item_adapter: TypeAdapter,
        listuple_class: type,
    ):
        self.item_adapter = item_adapter
        self.listuple_class = listuple_class
        self.empty_listuple = listuple_class()

    def default_expr(self) -> ExprLike:
        return "()"

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        listuple_class_local = Expr.local("_lstpl?", self.listuple_class)
        empty_listuple_local = Expr.local("_emp?", self.empty_listuple)
        return Expr.join(
            "(",
            arg_expr,
            " if ",
            arg_expr,
            ".__class__ is ",
            listuple_class_local,
            " else (",
            listuple_class_local,
            "([",
            self.item_adapter.to_frozen_expr("_e"),
            " for _e in ",
            arg_expr,
            "]) or ",
            empty_listuple_local,
            "))",
        )

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> ExprLike:
        # Can't use arg_expr, an empty iterable is not guaranteed to evaluate to False.
        return attr_expr

    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> ExprLike:
        item_to_json = self.item_adapter.to_json_expr("_e", readable)
        if Expr.join(item_to_json) == Expr.join("_e"):
            return in_expr
        return Expr.join(
            "[",
            item_to_json,
            " for _e in ",
            in_expr,
            "]",
        )

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        listuple_class_local = Expr.local("_lstpl?", self.listuple_class)
        empty_listuple_local = Expr.local("_emp?", self.empty_listuple)
        return Expr.join(
            listuple_class_local,
            "([",
            self.item_adapter.from_json_expr("_e"),
            " for _e in ",
            json_expr,
            "] or ",
            empty_listuple_local,
            ")",
        )

    def finalize(
        self,
        resolve_type_fn: Callable[[spec.Type], "TypeAdapter"],
    ) -> None:
        self.item_adapter.finalize(resolve_type_fn)


_ItemAndKeyAttributes = tuple[TypeAdapter, tuple[str, ...]]
_ItemToArrayAdapter = WeakValueDictionary[_ItemAndKeyAttributes, _ArrayAdapter]

_item_to_array_adapter: _ItemToArrayAdapter = WeakValueDictionary()


def _new_listuple_class() -> type:
    class Listuple(Generic[Item], tuple[Item, ...]):
        __slots__ = ()

    return Listuple


def _new_keyed_items_class(key_attributes: tuple[str, ...], default_expr: ExprLike):
    key_items = make_function(
        name="key_items",
        params=["items"],
        body=[
            "ret = {}",
            "for item in items:",
            f"  ret[item.{'.'.join(key_attributes)}] = item",
            "return ret",
        ],
    )

    default = make_function(
        name="get_default",
        params="",
        body=[Line.join("return ", default_expr)],
    )()

    class KeyedItemsImpl(KeyedItems[Item, Key]):
        # nonempty __slots__ not supported for subtype of 'tuple'

        _key_to_item: dict[Key, Item]

        def find(self, key: Key) -> Optional[Item]:
            try:
                key_to_item = self._key_to_item
            except AttributeError:
                key_to_item = key_items(self)
                object.__setattr__(self, "_key_to_item", key_to_item)
            return key_to_item.get(key)

        def find_or_default(self, key: Key) -> Any:
            return self.find(key) or default

        def __setattr__(self, name: str, value: Any):
            raise FrozenInstanceError(self.__class__.__qualname__)

        def __delattr__(self, name: str):
            raise FrozenInstanceError(self.__class__.__qualname__)

    return KeyedItemsImpl
