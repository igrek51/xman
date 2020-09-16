from xman.header import has_header, get_header
from xman.request import HttpRequest
from xman.response import HttpResponse

response1 = HttpResponse(status_code=500, headers={
    "Connection": "close",
    "Content-Length": "132",
    "Content-Type": "application/json; charset=UTF-8",
}, content='{"payload":"val"}\n'.encode())
empty_response = HttpResponse(status_code=500, headers={}, content=b'')


def test_response_data():
    response1.log('> sending', verbose=0)
    response1.log('> sending', verbose=1)
    response1.log('> sending', verbose=2)
    assert response1.json() == {'payload': 'val'}
    assert empty_response.json() is None


def test_response_transform():
    request1 = HttpRequest(method='POST', path='/proxy/auth?param=47', content=b'{"var":"val"}',
                           requestline='POST /auth HTTP/1.1', client_addr='127.0.0.1', client_port=41766,
                           timestamp=1600269808.01,
                           headers={"content-length": "136", "content-type": "application/json"})

    def response_transformer(request: HttpRequest, response: HttpResponse) -> HttpResponse:
        if response.status_code == 500:
            response.status_code = 200
        return response

    transformed = response1.transform(response_transformer, request1)

    assert transformed.status_code == 200
    assert response1 != transformed

    transformed2 = response1.transform(response_transformer, request1)
    assert transformed2 == transformed

    assert response1.transform(None, request1) == response1


def test_get_header():
    assert has_header(response1.headers, 'content-length')
    assert has_header(response1.headers, 'Content-Length')
    assert not has_header(response1.headers, 'Host')

    assert get_header(response1.headers, 'content-length', 'default') == '132'
    assert get_header(response1.headers, 'Content-Length', 'default') == '132'
    assert get_header(response1.headers, 'Host', 'default') == 'default'


def test_set_response():
    empty_response.set_content('dup')
    assert empty_response.content.decode() == 'dup'
    assert get_header(empty_response.headers, 'content-Length', '') == '3'

    empty_response.set_json({'name': 'vall'})
    assert get_header(empty_response.headers, 'Content-Type', '') == 'application/json'
    assert empty_response.json() == {'name': 'vall'}
