import requests
import urllib3
from nuclear.sublog import log, wrap_context, logerr

from .request import HttpRequest
from .response import HttpResponse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def proxy_request(request: HttpRequest, default_url: str, timeout: int, verbose: int) -> HttpResponse:
    dst_url = request.dst_url if request.dst_url else default_url
    with logerr():
        with wrap_context('proxying to URL', dst_url=dst_url, path=request.path, content=request.content):
            url = f'{dst_url}{request.path}'
            if verbose:
                log.debug(f'>> proxying to', url=url)
            response = requests.request(request.method, url, verify=False, allow_redirects=False, stream=False,
                                        timeout=timeout, headers=request.headers, data=request.content)
            content: bytes = response.content
            return HttpResponse(status_code=response.status_code, headers=dict(response.headers), content=content)

    # Bad Gateway response
    error_msg = f'Proxying failed: {dst_url}'
    return HttpResponse(status_code=502, headers={
        'X-Man-Error': 'proxying failed',
    }, content=error_msg.encode())
