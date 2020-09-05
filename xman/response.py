import json
from http.client import responses
from typing import Dict, Callable, Any, Optional

from dataclasses import dataclass
from nuclear.sublog import log

from .request import HttpRequest


@dataclass
class HttpResponse(object):
    status_code: int
    headers: Dict[str, str]
    content: bytes

    def log(self, prefix: str, verbose: bool) -> 'HttpResponse':
        status = f'{self.status_code} {responses[self.status_code]}'
        if verbose:
            log.debug(f'{prefix}', status=status, headers=self.headers, content='\n' + self.content.decode())
        else:
            log.debug(f'{prefix}', status=status)
        return self

    @staticmethod
    def from_json(data: dict) -> 'HttpResponse':
        data['content'] = data.get('content').encode()
        return HttpResponse(**data)

    def transform(self, transformer: Optional[Callable[[HttpRequest, 'HttpResponse'], 'HttpResponse']],
                  request: HttpRequest) -> 'HttpResponse':
        if transformer is None:
            return self
        cloned = HttpResponse(
            status_code=self.status_code,
            headers=self.headers,
            content=self.content,
        )
        return transformer(request, cloned)

    def set_content(self, content: str) -> 'HttpResponse':
        self.content = content.encode()
        self.headers['Content-Length'] = str(len(self.content))
        return self

    def set_json(self, obj: Any) -> 'HttpResponse':
        self.content = json.dumps(obj).encode()
        self.headers['Content-Length'] = str(len(self.content))
        self.headers['Content-Type'] = 'application/json'
        return self

    def json(self) -> Any:
        if len(self.content) == 0:
            return None
        return json.loads(self.content)
