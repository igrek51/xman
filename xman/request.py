import json
from typing import Dict, Callable, Any, Optional
from urllib import parse

from dataclasses import dataclass, asdict
from dataclasses import field
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
    """Set to redirect particular request somewhere else"""
    forward_url: Optional[str] = None
    """Custom labels marked while processing request"""
    metadata: Dict[str, str] = field(default_factory=lambda: dict())

    @staticmethod
    def from_json(data: dict) -> 'HttpRequest':
        data['content'] = data.get('content').encode('utf-8')
        return HttpRequest(**data)

    def to_json(self) -> dict:
        d = asdict(self)
        if not self.forward_url:
            del d['forward_url']
        if not self.metadata:
            del d['metadata']
        return d

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
            forward_url=self.forward_url,
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
