import json
from typing import Dict, Callable, Any, Optional

from dataclasses import dataclass
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

    @staticmethod
    def from_json(data: dict) -> 'HttpRequest':
        data['content'] = data.get('content').encode('utf-8')
        return HttpRequest(**data)

    def log(self, verbose: bool):
        if not verbose:
            log.info(f'< Incoming: {self.requestline}')
        elif self.content:
            log.info(f'< Incoming: {self.requestline}', headers=self.headers, content='\n'+self.content.decode('utf-8'))
        else:
            log.info(f'< Incoming: {self.requestline}', headers=self.headers)

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
        )
        return transformer(cloned)

    def json(self) -> Any:
        if len(self.content) == 0:
            return None
        return json.loads(self.content)
