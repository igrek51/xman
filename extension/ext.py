import re
from typing import List, Callable, Tuple

from nuclear.sublog import log

from middler.request import HttpRequest


def _transformer_shorten_path(request: HttpRequest) -> HttpRequest:
    if request.path.startswith('/path/'):
        match = re.search(r'^/path/(.+?)(/[a-z]+)(/.*)', request.path)
        if match:
            request.path = match.group(3)
            log.debug('request path transformed', path=request.path)
    return request


transformers: List[Callable[[HttpRequest], HttpRequest]] = [
    _transformer_shorten_path,
]


def _default_request_traits(request: HttpRequest) -> Tuple:
    return request.method, request.path, request.content, sorted(request.headers.items(), key=lambda t: t[0])


request_traits_extractor: Callable[[HttpRequest], Tuple] = _default_request_traits
