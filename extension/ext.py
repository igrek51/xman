import re
from typing import List, Callable, Tuple, Optional

from nuclear.sublog import log

from middler.cache import sorted_dict_trait
from middler.config import Config
from middler.request import HttpRequest
from middler.response import HttpResponse


def _request_shorten_path(request: HttpRequest) -> HttpRequest:
    if request.path.startswith('/path/'):
        match = re.search(r'^/path/(.+?)(/[a-z]+)(/.*)', request.path)
        if match:
            request.path = match.group(3)
            log.debug('request path transformed', path=request.path)
    return request


def _default_cache_traits(request: HttpRequest) -> Tuple:
    return request.method, request.path, request.content, sorted_dict_trait(request.headers)


def _default_cache_predicate(request: HttpRequest) -> bool:
    return True


"""Mappers applied on every request before further processing"""
request_transformers: List[Callable[[HttpRequest], HttpRequest]] = [
    _request_shorten_path,
]

"""Mappers applied on every response after processing"""
response_transformers: List[Callable[[HttpResponse], HttpResponse]] = [
]

"""Gets tuple denoting request uniqueness. Requests with same results are treated as the same when caching."""
cache_traits_extractor: Callable[[HttpRequest], Tuple] = _default_cache_traits

"""Indicates whether particular request should be cached or not"""
cache_predicate: Callable[[HttpRequest], bool] = _default_cache_predicate

"""Returns custom config overriding defaults and provided args"""
config_builder: Optional[Callable[[...], Config]] = None
