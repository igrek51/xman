import re

from nuclear.sublog import log

from .request import HttpRequest


def replace_request_path(request: HttpRequest, match_regex: str, replace_regex: str) -> HttpRequest:
    """
    Replace request path applying Regex.
    Example:
        replace_request_path(request, r'^/path/(.+?)(/[a-z]+)(/.*)', r'\3')
    """
    matcher = re.compile(match_regex)
    if matcher.match(request.path):
        request.path = matcher.sub(replace_regex, request.path)
        log.debug('request path transformed', path=request.path)
    return request
