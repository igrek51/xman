from typing import Dict, List, Callable

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

    def transform(self, transformers: List[Callable[['HttpRequest'], 'HttpRequest']]) -> 'HttpRequest':
        transformed = self
        for transformer in transformers:
            transformed = transformer(transformed)
        return transformed
