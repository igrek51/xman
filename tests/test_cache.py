import os
from pathlib import Path

from xman.cache import RequestCache
from xman.config import Config
from xman.extension import Extensions
from xman.request import HttpRequest
from xman.response import HttpResponse

request1 = HttpRequest(method='GET', path='/', content=b'', requestline='GET / HTTP/1.1', client_addr='127.0.0.1',
                       client_port=41696, timestamp=100.1, headers={"accept": "*/*",
                                                                    "accept-encoding": "gzip, deflate, br",
                                                                    "accept-language": "en-US,en;q=0.9",
                                                                    "connection": "close",
                                                                    "content-type": "application/json",
                                                                    "host": "localhost:8080",
                                                                    "referer": "https://localhost:8080/",
                                                                    })
response1 = HttpResponse(status_code=200, headers={
    "Connection": "close",
    "Content-Length": "132",
    "Content-Type": "application/json; charset=UTF-8",
}, content='{"payload":"val"}\n'.encode())

request2 = HttpRequest(method='POST', path='/auth', content=b'{"var":{"val"}}', dst_url='https://127.0.0.1:9000',
                       requestline='POST /auth HTTP/1.1', client_addr='127.0.0.1', client_port=41766,
                       timestamp=1600269808.01, headers={"accept": "*/*",
                                                         "accept-encoding": "gzip, deflate, br",
                                                         "accept-language": "en-US,en;q=0.9",
                                                         "connection": "close",
                                                         "content-length": "136",
                                                         "content-type": "application/json",
                                                         })
response2 = HttpResponse(status_code=201, headers={
    "Connection": "close",
    "Content-Length": "19",
    "Content-Type": "application/json",
}, content='{"payload":"value"}'.encode())


def test_loading_cache():
    cache = RequestCache(Extensions(), Config(
        record_file='tests/res/tape_read.json',
        replay=True,
    ))

    assert len(cache.cache) == 2
    assert cache.has_cached_response(request1)
    assert cache.has_cached_response(request2)
    assert cache.replay_response(request1) == response1
    assert cache.replay_response(request2) == response2

    request_no = HttpRequest(method='GET', path='/', content=b'', headers={}, requestline='', client_addr='',
                             client_port=0, timestamp=0)
    assert not cache.has_cached_response(request_no)


def test_clear_cache():
    cache = RequestCache(Extensions(), Config(
        record_file='tests/res/tape_read.json',
        replay_clear_cache=True,
        replay_clear_cache_seconds=10,
        verbose=2,
    ))

    assert len(cache.cache) == 2
    cache.clear_old()
    assert len(cache.cache) == 0


def test_read_from_empty():
    cache = RequestCache(Extensions(), Config(
        record_file='tests/res/tape_empty.json',
    ))
    assert len(cache.cache) == 0


def test_read_from_non_existing():
    cache = RequestCache(Extensions(), Config(
        record_file='tests/res/tape_not_existing.json',
    ))
    assert len(cache.cache) == 0


def test_replay_disabled():
    cache = RequestCache(Extensions(), Config(
        record_file='tests/res/tape_read.json',
        replay=False,
    ))

    assert len(cache.cache) == 2
    assert not cache.has_cached_response(request1)


def test_save_new():
    Path('tests/res/tape_save.json').unlink()
    cache = RequestCache(Extensions(), Config(
        record_file='tests/res/tape_save.json',
        record=True,
    ))
    assert len(cache.cache) == 0
    assert cache.saving_enabled(request1, response1)
    cache.save_response(request1, response1)
    assert cache.saving_enabled(request2, response2)
    cache.save_response(request2, response2)

    saved = Path('tests/res/tape_save.json').read_text()
    expected = Path('tests/res/tape_read.json').read_text()
    assert saved == expected
