import inspect
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar, Union, cast

from soia._impl.method import Method, Request, Response

RequestHeaders = TypeVar("RequestHeaders")

ResponseHeaders = TypeVar("ResponseHeaders")


@dataclass(frozen=True)
class _MethodImpl(Generic[Request, Response, RequestHeaders, ResponseHeaders]):
    method: Method[Request, Response]
    impl: Callable[
        # Parameters
        [Request, RequestHeaders, ResponseHeaders],
        # Return type
        Union[Response, Awaitable[Response]],
    ]


@dataclass(frozen=True)
class RawServiceResponse:
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


@dataclass()
class _HandleRequestFlow(Generic[Request, Response, RequestHeaders, ResponseHeaders]):
    req_body: str
    req_headers: RequestHeaders
    res_headers: ResponseHeaders
    number_to_method_impl: dict[
        int, _MethodImpl[Any, Any, RequestHeaders, ResponseHeaders]
    ]
    _format: str = ""

    def run(self) -> RawServiceResponse:
        req_impl_pair_or_raw_response = self._parse_request()
        if isinstance(req_impl_pair_or_raw_response, RawServiceResponse):
            return req_impl_pair_or_raw_response
        req, method_impl = req_impl_pair_or_raw_response
        try:
            res = method_impl.impl(req, self.req_headers, self.res_headers)
        except Exception as e:
            return RawServiceResponse(f"server error: {e}", "server-error")
        if inspect.isawaitable(res):
            raise TypeError("Method implementation must be synchronous")
        return self._response_to_json(res, method_impl)

    async def run_async(self) -> RawServiceResponse:
        req_impl_pair_or_raw_response = self._parse_request()
        if isinstance(req_impl_pair_or_raw_response, RawServiceResponse):
            return req_impl_pair_or_raw_response
        req, method_impl = req_impl_pair_or_raw_response
        try:
            res: Any = method_impl.impl(req, self.req_headers, self.res_headers)
            if inspect.isawaitable(res):
                res = await res
        except Exception as e:
            return RawServiceResponse(f"server error: {e}", "server-error")
        return self._response_to_json(res, method_impl)

    def _parse_request(
        self,
    ) -> Union[
        tuple[Any, _MethodImpl[Request, Response, RequestHeaders, ResponseHeaders]],
        RawServiceResponse,
    ]:
        if self.req_body == "list":

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
                        for method_impl in self.number_to_method_impl.values()
                    ]
                },
                indent=2,
            )
            return RawServiceResponse(json_code, "ok-json")

        parts = self.req_body.split(":", 3)
        if len(parts) != 4:
            return RawServiceResponse(
                "bad request: invalid request format", "bad-request"
            )
        method_name = parts[0]
        method_number_str = parts[1]
        self.format = parts[2]
        request_data = parts[3]
        try:
            method_number = int(method_number_str)
        except Exception:
            return RawServiceResponse(
                "bad request: can't parse method number", "bad-request"
            )
        method_impl = self.number_to_method_impl.get(method_number)
        if not method_impl:
            return RawServiceResponse(
                f"bad request: method not found: {method_name}; number: {method_number}",
                "bad-request",
            )
        try:
            req: Any = method_impl.method.request_serializer.from_json_code(
                request_data
            )
        except Exception as e:
            return RawServiceResponse(
                f"bad request: can't parse JSON: {e}", "bad-request"
            )
        return (req, method_impl)

    def _response_to_json(
        self,
        res: Response,
        method_impl: _MethodImpl[Request, Response, RequestHeaders, ResponseHeaders],
    ) -> RawServiceResponse:
        try:
            res_json = method_impl.method.response_serializer.to_json_code(
                res, readable=(self.format == "readable")
            )
        except Exception as e:
            return RawServiceResponse(
                f"server error: can't serialize response to JSON: {e}", "server-error"
            )
        return RawServiceResponse(res_json, "ok-json")


class _ServiceImpl(Generic[RequestHeaders, ResponseHeaders]):
    _number_to_method_impl: dict[
        int, _MethodImpl[Any, Any, RequestHeaders, ResponseHeaders]
    ]

    def __init__(self):
        self._number_to_method_impl = {}

    def add_method(
        self,
        method: Method[Request, Response],
        impl: Union[
            # Sync
            Callable[[Request], Response],
            Callable[[Request, RequestHeaders], Response],
            Callable[[Request, RequestHeaders, ResponseHeaders], Response],
            # Async
            Callable[[Request], Awaitable[Response]],
            Callable[[Request, RequestHeaders], Awaitable[Response]],
            Callable[[Request, RequestHeaders, ResponseHeaders], Awaitable[Response]],
        ],
    ) -> None:
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

    def handle_request(
        self,
        req_body: str,
        req_headers: RequestHeaders,
        res_headers: ResponseHeaders,
    ) -> RawServiceResponse:
        flow = _HandleRequestFlow(
            req_body=req_body,
            req_headers=req_headers,
            res_headers=res_headers,
            number_to_method_impl=self._number_to_method_impl,
        )
        return flow.run()

    async def handle_request_async(
        self,
        req_body: str,
        req_headers: RequestHeaders,
        res_headers: ResponseHeaders,
    ) -> RawServiceResponse:
        flow = _HandleRequestFlow(
            req_body=req_body,
            req_headers=req_headers,
            res_headers=res_headers,
            number_to_method_impl=self._number_to_method_impl,
        )
        return await flow.run_async()


class Service(Generic[RequestHeaders, ResponseHeaders]):
    """Wraps around the implementation of a soia service on the server side.

    Usage: call '.add_method()' to register method implementations, then call
    '.handle_request()' from the function called by your web framework when an
    HTTP request is received at your service's endpoint.

    Example with Flask:

        from flask import Response, request
        from werkzeug.datastructures import Headers


        s = soia.Service[Headers, Headers]()
        s.add_method(...)
        s.add_method(...)

        @app.route("/myapi", methods=["GET", "POST"])
        def myapi():
            if request.method == "POST":
                req_body = request.get_data(as_text=True)
            else:
                query_string = request.query_string.decode("utf-8")
                req_body = urllib.parse.unquote(query_string)
            req_headers = request.headers
            res_headers = Headers()
            raw_response = s.handle_request(req_body, req_headers, res_headers)
            return Response(
                raw_response.data,
                status=raw_response.status_code,
                content_type=raw_response.content_type,
                headers=res_headers,
            )
    """

    _impl: _ServiceImpl[RequestHeaders, ResponseHeaders]

    def __init__(self):
        self._impl = _ServiceImpl[RequestHeaders, ResponseHeaders]()

    def add_method(
        self,
        method: Method[Request, Response],
        impl: Union[
            Callable[[Request], Response],
            Callable[[Request, RequestHeaders], Response],
            Callable[[Request, RequestHeaders, ResponseHeaders], Response],
        ],
    ) -> None:
        self._impl.add_method(method, impl)

    def handle_request(
        self,
        req_body: str,
        req_headers: RequestHeaders,
        res_headers: ResponseHeaders,
    ) -> RawServiceResponse:
        return self._impl.handle_request(req_body, req_headers, res_headers)


class ServiceAsync(Generic[RequestHeaders, ResponseHeaders]):
    _impl: _ServiceImpl[RequestHeaders, ResponseHeaders]

    def __init__(self):
        self._impl = _ServiceImpl[RequestHeaders, ResponseHeaders]()

    def add_method(
        self,
        method: Method[Request, Response],
        impl: Union[
            # Sync
            Callable[[Request], Response],
            Callable[[Request, RequestHeaders], Response],
            Callable[[Request, RequestHeaders, ResponseHeaders], Response],
            # Async
            Callable[[Request], Awaitable[Response]],
            Callable[[Request, RequestHeaders], Awaitable[Response]],
            Callable[[Request, RequestHeaders, ResponseHeaders], Awaitable[Response]],
        ],
    ) -> None:
        self._impl.add_method(method, impl)

    async def handle_request(
        self,
        req_body: str,
        req_headers: RequestHeaders,
        res_headers: ResponseHeaders,
    ) -> RawServiceResponse:
        return await self._impl.handle_request_async(req_body, req_headers, res_headers)
