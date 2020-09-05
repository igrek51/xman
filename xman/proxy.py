import requests
import urllib3
from nuclear.sublog import log, wrap_context

from .request import HttpRequest
from .response import HttpResponse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def proxy_request(request: HttpRequest, base_url: str) -> HttpResponse:
    with wrap_context('proxying to destination', base_url=base_url):
        url = f'{base_url}{request.path}'
        log.debug(f'>> proxying to', url=url)
        response = requests.request(request.method, url, verify=False, allow_redirects=False, stream=False,
                                    timeout=10, headers=request.headers, data=request.content)
        content: bytes = response.content
        return HttpResponse(status_code=response.status_code, headers=dict(response.headers), content=content)
