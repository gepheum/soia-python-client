from collections.abc import Callable
from typing import Protocol

from soialib import spec
from soialib.impl.function_maker import ExprLike


class TypeAdapter(Protocol):
    def default_expr(self) -> ExprLike:
        """
        The default value for T.
        """
        ...

    def to_frozen_expr(self, arg_expr: ExprLike) -> ExprLike:
        """
        Transforms the argument passed to the constructor of a frozen class into a
        frozen value which will be assigned to the attribute of the frozen object.

        The type of the returned expression must be T even if the argument does not have
        the expected type. Ideally, the expression should raise an error in the latter
        case.
        """
        ...

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> ExprLike:
        """
        Returns an expression which evaluates to true if the given value is *not* the
        default value for T.
        This expression is inserted in the constructor of a frozen class, after the
        attribute has been assigned from the result of freezing arg_expr.
        If possible, an implemtation should try to use arg_expr instead of attr_expr as
        it offers a marginal performance advantage ('x' vs 'self.x').
        """
        ...

    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> ExprLike:
        """
        Returns an expression which can be passed to 'json.dumps()' in order to
        serialize the given T into JSON format.
        The JSON flavor (dense versus readable) is given by the 'readable' arg.
        """
        ...

    def from_json_expr(self, json_expr: ExprLike) -> ExprLike:
        """
        Transforms 'json_expr' into a T.
        The 'json_expr' arg is obtained by calling 'json.loads()'.
        """
        ...

    def finalize(
        self,
        resolve_type_fn: Callable[[spec.Type], "TypeAdapter"],
    ) -> None: ...
