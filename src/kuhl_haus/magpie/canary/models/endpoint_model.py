from dataclasses import dataclass, field
from typing import Any, Optional, Sequence
from urllib import parse


@dataclass()
class EndpointModel:
    mnemonic: str
    hostname: str
    scheme: Optional[str] = "https"
    port: Optional[int] = 443
    path: Optional[str] = field(default="/")
    query: Optional[Sequence[tuple[Any, Any]]] = None
    fragment: Optional[str] = None
    verb: Optional[str] = "GET"
    body: Optional[str] = None
    healthy_status_code: Optional[int] = 200
    response_format: Optional[str] = "text"
    status_key: Optional[str] = None
    healthy_status: Optional[str] = None
    version_key: Optional[str] = None
    connect_timeout: Optional[float] = 7
    read_timeout: Optional[float] = 7
    ignore: Optional[bool] = False
    health_check: Optional[bool] = False
    tls_check: Optional[bool] = False
    dns_check: Optional[bool] = False

    def __post_init__(self):
        """
        __post_init__

        Automatically called after the dataclass initialization to perform additional processing.

        Raises
        ------
        None
        """
        self.path = self.__normalize_path(self.path)

    @staticmethod
    def __normalize_path(path: str) -> str:
        if not path:
            path = "/"
        elif not path.startswith("/"):
            path = f"/{path}"
        # Replace multiple slashes with a single slash
        while '//' in path:
            path = path.replace('//', '/')
        return path

    @property
    def url(self) -> str:
        path = self.__normalize_path(self.path)
        if self.query:
            query_string = parse.urlencode(self.query)
            path = parse.urljoin(path, f"?{query_string}")
        if self.fragment:
            path = parse.urljoin(path, f"#{self.fragment}")
        return f"{self.scheme}://{self.hostname}:{self.port}{path}"
