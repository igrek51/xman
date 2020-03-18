import re

from nuclear.sublog import log

from midman.request import HttpRequest


def transformer_shorten_path(request: HttpRequest) -> HttpRequest:
    if request.path.startswith('/proxy/'):
        match = re.search(r'^/proxy/(.+?)(/[a-z]+)(/.*)', request.path)
        if match:
            request.path = match.group(3)
            log.debug('request path transformed', path=request.path)
    return request


transformers = [
    transformer_shorten_path,
]
