import re
from typing import Callable, List
from importlib.machinery import SourceFileLoader
from nuclear.sublog import log
from midman.request import HttpRequest


def transformer_shorten_path(request: HttpRequest) -> HttpRequest:
    if request.path.startswith('/proxy/'):
        match = re.search(r'^/proxy/(.+?)(/[a-z]+)(/.*)', request.path)
        if match:
            request.path = match.group(3)
            log.debug('request transformed', path=request.path)
    return request


def load_transformers(extension_path: str) -> List[Callable[[HttpRequest], HttpRequest]]:
    if not extension_path:
        return []

    log.debug(f'loading extensions', path=extension_path)

    ext_module = SourceFileLoader("midman.transformer", extension_path).load_module()
    transformers = ext_module.transformers

    names = ','.join([t.__name__ for t in transformers])
    log.debug(f'loaded transformers', count=len(transformers), names=names)
    return transformers
