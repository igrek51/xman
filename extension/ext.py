from typing import Tuple

from nuclear.sublog import log

from middler.cache import sorted_dict_trait
from middler.config import Config
from middler.request import HttpRequest
from middler.response import HttpResponse
from middler.transform import replace_request_path


def transform_request(request: HttpRequest) -> HttpRequest:
    """Transforms each incoming Request before further processing (caching, forwarding)"""
    return replace_request_path(request, r'^/path/(.+?)(/[a-z]+)(/.*)', r'\3')


def transform_response(request: HttpRequest, response: HttpResponse) -> HttpResponse:
    """Transforms each Response before sending it"""
    if request.path.startswith('/api'):
        log.debug('Found Ya', path=request.path)
        response = response.set_content('{"payload": "error"}"')
    return response


def can_be_cached(request: HttpRequest) -> bool:
    """Indicates whether particular request could be saved / restored from cache"""
    return request.method in {'get', 'post'}


def cache_request_traits(request: HttpRequest) -> Tuple:
    """Gets tuple denoting request uniqueness. Requests with same results are treated as the same when caching."""
    return request.method, request.path, request.content, sorted_dict_trait(request.headers)


def override_config(config: Config):
    """Overrides default parameters in config"""
    config.verbose = True
