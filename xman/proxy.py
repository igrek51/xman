import requests
import urllib3
from nuclear.sublog import log, wrap_context, logerr

from .request import HttpRequest
from .response import HttpResponse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

bad_gateway_response = HttpResponse(status_code=502, headers={'X-Xman-Error': 'proxying failed'}, content=b'')


def proxy_request(request: HttpRequest, base_url: str, timeout: int, verbose: int) -> HttpResponse:
    with logerr():
        with wrap_context('proxying to destination', dst_url=base_url, path=request.path, content=request.content):
            url = f'{base_url}{request.path}'
            if verbose:
                log.debug(f'>> proxying to', url=url)
            response = requests.request(request.method, url, verify=False, allow_redirects=False, stream=False,
                                        timeout=timeout, headers=request.headers, data=request.content)
            content: bytes = response.content
            return HttpResponse(status_code=response.status_code, headers=dict(response.headers), content=content)

    return bad_gateway_response
