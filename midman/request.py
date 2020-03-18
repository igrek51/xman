from datetime import datetime
from typing import Dict, Tuple

from dataclasses import dataclass


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

    def traits(self) -> Tuple:
        return self.method, self.path, self.content, str(self.headers)

    def show(self, prefix: str):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'\n{prefix} [{current_time}] {self.requestline} {self.headers}')
        if self.content:
            decoded: str = self.content.decode('utf-8')
            print(f'{prefix} {decoded}')

    def __hash__(self):
        return hash(self.traits())

    def __eq__(self, other):
        return self.traits() == other.traits()

    @staticmethod
    def from_json(data: dict) -> 'HttpRequest':
        data['content'] = data.get('content').encode('utf-8')
        return HttpRequest(**data)
