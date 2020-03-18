import json
import sys
from http.server import SimpleHTTPRequestHandler
from typing import Dict, Iterable, Sequence, Callable, List

import requests
import urllib3
from nuclear.sublog import log, log_error, wrap_context

from midman.cache import RequestCache, now_seconds, CacheEntry, EnhancedJSONEncoder
from midman.config import Config
from midman.request import HttpRequest
from midman.response import HttpResponse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RequestHandler(SimpleHTTPRequestHandler):
    transformers: List[Callable[[HttpRequest], HttpRequest]]
    request_cache: RequestCache

    def handle_request(self):
        with log_error():
            with wrap_context('handling request'):
                self.connection.settimeout(10)
                incoming_request = self.incoming_request()
                incoming_request.show('<')
                response = self.generate_response(incoming_request)
                self.respond_to_client(response)

    def generate_response(self, incoming_request: HttpRequest) -> HttpResponse:
        log.debug('transformers', transformers=self.transformers)
        for transformer in self.transformers:
            incoming_request = transformer(incoming_request)
            log.debug('request transformed', path=incoming_request.path)

        request_hash = hash(incoming_request)

        if Config.replay_clear_cache:
            self.request_cache.clear_old_cache()

        if request_hash in self.request_cache.cache and Config.replay:
            if Config.replay_throttle:
                print(f'> Sending throttled response, hash: #{request_hash}')
                return too_many_requests_response.show('>')
            print(f'> Sending cached response, hash: #{request_hash}')
            cached = self.request_cache.cache[request_hash]
            return cached.response.show('>')

        response: HttpResponse = send_to(incoming_request, base_url=f'{Config.dst_url}').show('<<')
        print(f'> forwarding response back to client {incoming_request.client_addr}:{incoming_request.client_port}')

        if Config.record or Config.replay:
            self.save_response(incoming_request, request_hash, response)

        return response

    def incoming_request(self) -> HttpRequest:
        headers_dict = {parsed_line[0]: parsed_line[1] for parsed_line in self.headers.items()}
        method = self.command.lower()
        content_len = int(headers_dict.get('Content-Length', 0))
        content: bytes = self.rfile.read(content_len) if content_len else b''
        return HttpRequest(requestline=self.requestline, method=method, path=self.path, headers=headers_dict,
                           content=content, client_addr=self.client_address[0], client_port=self.client_address[1],
                           timestamp=now_seconds())

    def respond_to_client(self, response: HttpResponse):
        self.send_response_only(response.status_code)

        if 'Content-Encoding' in response.headers:
            del response.headers['Content-Encoding']
            print('removing Content-Encoding header')

        for name, value in response.headers.items():
            self.send_header(name, value)
        self.end_headers()

        if Config.allow_chunking and response.headers.get('Transfer-Encoding') == 'chunked':
            self.send_chunked_response(chunks(response.content, 512))
        else:
            self.wfile.write(response.content)
        self.close_connection = True

    def send_chunked_response(self, content_chunks: Iterable[bytes]):
        for chunk in content_chunks:
            tosend = ('%X' % len(chunk)).encode('utf-8') + b'\r\n' + chunk + b'\r\n'
            self.wfile.write(tosend)
        self.wfile.write('0\r\n\r\n'.encode('utf-8'))

    def respond_json(self, response: Dict):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def save_response(self, incoming_request: HttpRequest, request_hash: int, response: HttpResponse):
        if request_hash not in self.request_cache.cache:
            self.request_cache.cache[request_hash] = CacheEntry(incoming_request, response)
            if Config.record and Config.record_file:
                with open(Config.record_file, 'w') as f:
                    serializable = list(self.request_cache.cache.values())
                    json.dump(serializable, f, sort_keys=True, indent=4, cls=EnhancedJSONEncoder)
            print(
                f'+ new request-response recorded, hash: #{request_hash} [{len(self.request_cache.cache)} entries in total]')

    def do_GET(self):
        self.dev_var() or self.handle_request()

    def do_POST(self):
        self.dev_var() or self.handle_request()

    def do_PUT(self):
        self.handle_request()

    def do_DELETE(self):
        self.handle_request()

    def do_HEAD(self):
        self.handle_request()

    def dev_var(self) -> bool:
        if self.path != '/dev/var':
            return False
        content_len = int(self.headers.get('Content-Length', 0))
        content = self.rfile.read(content_len) if content_len else ''
        if not content:
            return False
        payload = json.loads(content)
        var_name = payload.get('name')
        if not var_name:
            return False
        if self.command.lower() == 'POST':
            var_value = payload.get('value')
            setattr(sys.modules[__name__], var_name, var_value)
            print(f'variable {var_name} set to {var_value}')
        var_value = getattr(sys.modules[__name__], var_name)
        self.respond_json({'name': var_name, 'value': var_value})
        return True


too_many_requests_response = HttpResponse(status_code=429, headers={}, content=b'')


def send_to(request: HttpRequest, base_url: str) -> HttpResponse:
    url = f'{base_url}{request.path}'
    print(f'>> proxying to {url}')
    response = requests.request(request.method, url, verify=False, allow_redirects=True, stream=False,
                                timeout=10, headers=request.headers, data=request.content)
    content: bytes = response.content
    return HttpResponse(status_code=response.status_code, headers=dict(response.headers), content=content)


def chunks(lst: Sequence, n: int) -> Iterable:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
