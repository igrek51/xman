import json
from typing import Dict, Callable, Any, Optional
from urllib import parse

from dataclasses import dataclass, field
from nuclear.sublog import log


@dataclass
class HttpRequest(object):
    requestline: str
    method: str
    path: str
    headers: Dict[str, str]
    content: bytes
    client_addr: str
    client_port: int
    timestamp: float
    """set to redirect particular request somewhere else"""
    forward_to_url: Optional[str] = None
    """custom labels marked while processing request"""
    metadata: Dict[str, str] = field(default_factory=lambda: dict())

    @staticmethod
    def from_json(data: dict) -> 'HttpRequest':
        data['content'] = data.get('content').encode('utf-8')
        return HttpRequest(**data)

    def log(self, verbose: int):
        ctx = {}
        if verbose >= 2:
            ctx['headers'] = self.headers
            if self.content:
                ctx['content'] = '\n'+self.content.decode('utf-8')
        log.info(f'< Incoming {self.method} {self.path}', **ctx)

    def transform(self, transformer: Optional[Callable[['HttpRequest'], 'HttpRequest']]) -> 'HttpRequest':
        if transformer is None:
            return self
        cloned = HttpRequest(
            requestline=self.requestline,
            method=self.method,
            path=self.path,
            headers=self.headers,
            content=self.content,
            client_addr=self.client_addr,
            client_port=self.client_port,
            timestamp=self.timestamp,
            forward_to_url=self.forward_to_url,
            metadata=self.metadata,
        )
        return transformer(cloned)

    def json(self) -> Any:
        if len(self.content) == 0:
            return None
        return json.loads(self.content)

    @property
    def query_path(self) -> str:
        """Path without params"""
        split = parse.urlsplit(self.path)
        return split.path

    @property
    def query_params(self) -> Dict[str, str]:
        split = parse.urlsplit(self.path)
        path_params = dict(parse.parse_qsl(split.query))
        return path_params
