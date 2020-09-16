from xman.proxy import proxy_request
from xman.request import HttpRequest


def test_proxy_failed():
    request = HttpRequest(
        requestline='GET /',
        method='GET',
        path='/',
        content=b'',
        headers={},
        client_addr='127.0.0.1',
        client_port=9999,
        timestamp=0,
    )
    response = proxy_request(request, default_url='0.0.0.1:9999', timeout=1, verbose=2)
    assert response.status_code == 502
    assert 'Proxying failed' in response.content.decode()
