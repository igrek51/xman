from typing import Dict, Tuple

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

    def log(self):
        if self.content:
            log.info(f'< Incoming: {self.requestline}', headers=self.headers, content='\n'+self.content.decode('utf-8'))
        else:
            log.info(f'< Incoming: {self.requestline}', headers=self.headers)
