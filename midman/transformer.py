import re

from midman.request import HttpRequest


def transformer_shorten_path(request: HttpRequest) -> HttpRequest:
    if request.path.startswith('/proxy/'):
        match = re.search(r'^/proxy/(.+?)(/[a-z]+)(/.*)', request.path)
        if match:
            request.path = match.group(3)
    return request


transformers = [
    transformer_shorten_path,
]
