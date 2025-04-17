import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Generic, Literal, Protocol, TypeAlias, Union, cast

from soia._impl.method import Method, Request, Response


class RequestHeaders(Protocol):
    def __getitem__(self, key: str, /) -> str | None: ...


ResponseHeaders: TypeAlias = dict[str, str]


class Service:
    _number_to_method_impl: dict[int, "_MethodImpl"]

    def __init__(self):
        self._number_to_method_impl = {}

    def add_method(
        self,
        method: Method[Request, Response],
        impl: Union[
            Callable[[Request], Response],
            Callable[[Request, RequestHeaders], Response],
            Callable[[Request, RequestHeaders, ResponseHeaders], Response],
        ],
    ) -> "Service":
        signature = inspect.Signature.from_callable(impl)
        num_positional_params = 0
        for param in signature.parameters.values():
            if param.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.POSITIONAL_ONLY,
            ):
                num_positional_params += 1
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                raise ValueError("Method implementation cannot accept *args")
        if num_positional_params not in range(1, 4):
            raise ValueError(
                "Method implementation must accept 1 to 3 positional parameters"
            )

        def resolved_impl(
            req: Request, req_headers: RequestHeaders, res_headers: ResponseHeaders
        ) -> Response:
            if num_positional_params == 1:
                return cast(Callable[[Request], Response], impl)(req)
            elif num_positional_params == 2:
                return cast(Callable[[Request, RequestHeaders], Response], impl)(
                    req, req_headers
                )
            else:
                return cast(
                    Callable[[Request, RequestHeaders, ResponseHeaders], Response], impl
                )(req, req_headers, res_headers)

        number = method.number
        if number in self._number_to_method_impl:
            raise ValueError(
                f"Method with the same number already registered ({number})"
            )
        self._number_to_method_impl[number] = _MethodImpl(
            method=method,
            impl=resolved_impl,
        )
        return self

    @dataclass(frozen=True)
    class RawResponse:
        data: str
        type: Literal["ok-json", "bad-request", "server-error"]

        @property
        def status_code(self):
            if self.type == "ok-json":
                return 200
            elif self.type == "bad-request":
                return 400
            elif self.type == "server-error":
                return 500
            else:
                raise TypeError(f"Unknown response type: {self.type}")

        @property
        def content_type(self):
            if self.type == "ok-json":
                return "application/json"
            elif self.type == "bad-request" or self.type == "server-error":
                return "text/plain; charset=utf-8"
            else:
                raise TypeError(f"Unknown response type: {self.type}")

    def handle_request(
        self,
        req_body: str,
        req_headers: RequestHeaders,
        res_headers: ResponseHeaders | None,
    ) -> RawResponse:
        if req_body == "list":

            def method_to_json(method: Method) -> Any:
                return {
                    "method": method.name,
                    "number": method.number,
                    "request": method.request_serializer.type_descriptor.as_json(),
                    "response": method.response_serializer.type_descriptor.as_json(),
                }

            json_code = json.dumps(
                {
                    "methods": [
                        method_to_json(method_impl.method)
                        for method_impl in self._number_to_method_impl.values()
                    ]
                },
                indent=2,
            )
            return self.RawResponse(json_code, "ok-json")

        parts = req_body.split(":", 3)
        if len(parts) != 4:
            return self.RawResponse(
                "bad request: invalid request format", "bad-request"
            )
        method_name = parts[0]
        method_number_str = parts[1]
        format = parts[2]
        request_data = parts[3]
        try:
            method_number = int(method_number_str)
        except Exception:
            return self.RawResponse(
                "bad request: can't parse method number", "bad-request"
            )
        method_impl = self._number_to_method_impl.get(method_number)
        if not method_impl:
            return self.RawResponse(
                f"bad request: method not found: {method_name}; number: {method_number}",
                "bad-request",
            )

        try:
            req: Any = method_impl.method.request_serializer.from_json_code(
                request_data
            )
        except Exception as e:
            return self.RawResponse(
                f"bad request: can't parse JSON: {e}", "bad-request"
            )

        try:
            res: Any = method_impl.impl(req, req_headers, res_headers or {})
        except Exception as e:
            return self.RawResponse(f"server error: {e}", "server-error")

        try:
            res_json = method_impl.method.response_serializer.to_json_code(
                res, readable=(format == "readable")
            )
        except Exception as e:
            return self.RawResponse(
                f"server error: can't serialize response to JSON: {e}", "server-error"
            )

        return self.RawResponse(res_json, "ok-json")


@dataclass(frozen=True)
class _MethodImpl(Generic[Request, Response]):
    method: Method[Request, Response]
    impl: Callable[[Request, RequestHeaders, ResponseHeaders], Response]
