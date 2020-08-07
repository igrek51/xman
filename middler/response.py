from typing import Dict, List, Callable

from dataclasses import dataclass
from nuclear.sublog import log

from http.client import responses

from middler.request import HttpRequest


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

    def transform(self, transformers: List[Callable[[HttpRequest, 'HttpResponse'], 'HttpResponse']],
                  request: HttpRequest) -> 'HttpResponse':
        transformed = self
        for transformer in transformers:
            transformed = transformer(request, transformed)
        return transformed
