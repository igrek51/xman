from xman.header import has_header, get_header
from xman.request import HttpRequest

request1 = HttpRequest(method='POST', path='/proxy/auth?param=47', content=b'{"var":"val"}',
                       requestline='POST /auth HTTP/1.1', client_addr='127.0.0.1', client_port=41766,
                       timestamp=1600269808.01,
                       headers={"content-length": "136", "content-type": "application/json"})
empty_request = HttpRequest(method='GET', path='/', content=b'', requestline='GET / HTTP/1.1', client_addr='127.0.0.1',
                            client_port=41766, timestamp=0, headers={})


def test_request_data():
    request1.log(verbose=2)
    assert request1.query_path == '/proxy/auth'
    assert request1.query_params == {'param': '47'}
    assert request1.json() == {'var': 'val'}
    assert empty_request.json() is None


def test_request_transform():
    def request_transformer(request: HttpRequest) -> HttpRequest:
        if request.path.startswith('/proxy'):
            request.path = request.path[len('/proxy'):]
        return request

    transformed = request1.transform(request_transformer)

    assert transformed.path == '/auth?param=47'
    assert request1 != transformed

    transformed2 = request1.transform(request_transformer)
    assert transformed2 == transformed

    assert request1.transform(None) == request1


def test_get_header():
    assert has_header(request1.headers, 'content-length')
    assert has_header(request1.headers, 'Content-Length')
    assert not has_header(request1.headers, 'Connection')

    assert get_header(request1.headers, 'content-length', 'default') == '136'
    assert get_header(request1.headers, 'Content-Length', 'default') == '136'
    assert get_header(request1.headers, 'Connection', 'default') == 'default'
