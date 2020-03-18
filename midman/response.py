from typing import Dict

from dataclasses import dataclass


@dataclass
class HttpResponse(object):
    status_code: int
    headers: Dict[str, str]
    content: bytes

    def show(self, prefix: str) -> 'HttpResponse':
        print(prefix, self.status_code, self.headers)
        print(prefix, self.content.decode('utf-8'))
        return self

    @staticmethod
    def from_json(data: dict) -> 'HttpResponse':
        data['content'] = data.get('content').encode('utf-8')
        return HttpResponse(**data)
