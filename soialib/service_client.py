import http.client
from typing import Final, Mapping, TypeVar
from urllib.parse import urlparse

from soialib import Method

Request = TypeVar("Request")
Response = TypeVar("Response")


class ServiceClient:
    _scheme: Final[str]
    _host: Final[str]  # May include the port
    _path: Final[str]

    def __init__(self, service_url: str, use_https: bool = False):
        parsed_url = urlparse(service_url)
        if parsed_url.query:
            raise ValueError("Service URL must not contain a query string")
        scheme = parsed_url.scheme
        if scheme not in ["http", "https"]:
            raise ValueError("Service URL must start with http:// or https://")
        self._scheme = scheme
        self._host = parsed_url.netloc
        self._path = parsed_url.path

    def invoke_remote(
        self,
        method: Method[Request, Response],
        request: Request,
        headers: Mapping[str, str] = {},
    ) -> Response:
        request_json = method.request_serializer.to_json_code(request)
        body = ":".join(
            [
                method.name,
                str(method.number),
                "",
                request_json,
            ]
        )
        headers = {
            **headers,
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Length": str(len(body)),
        }
        if self._scheme == "https":
            conn = http.client.HTTPSConnection(self._host)
        else:
            conn = http.client.HTTPConnection(self._host)
        try:
            conn.request(
                "POST",
                self._path,
                body=body,
                headers=headers,
            )
            response = conn.getresponse()
            status_code = response.status
            content_type = response.getheader("Content-Type")
            response_data = response.read().decode("utf-8", errors="ignore")
        finally:
            conn.close()
        if status_code in range(200, 300):
            return method.response_serializer.from_json_code(response_data)
        else:
            message = f"HTTP response status {status_code}"
            if content_type == "text/plain":
                message = f"{message}: {response_data}"
            raise RuntimeError(message)
