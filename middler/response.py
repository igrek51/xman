from typing import Dict

from dataclasses import dataclass
from nuclear.sublog import log


@dataclass
class HttpResponse(object):
    status_code: int
    headers: Dict[str, str]
    content: bytes

    def log(self, prefix: str) -> 'HttpResponse':
        log.debug(f'{prefix}', status=self.status_code, headers=self.headers, content='\n'+self.content.decode('utf-8'))
        return self

    @staticmethod
    def from_json(data: dict) -> 'HttpResponse':
        data['content'] = data.get('content').encode('utf-8')
        return HttpResponse(**data)
