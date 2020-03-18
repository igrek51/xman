import json
import sys
from http.server import SimpleHTTPRequestHandler
from typing import Dict, Iterable, Sequence, Callable, List

from nuclear.sublog import log, log_error, wrap_context

from midman.cache import RequestCache, now_seconds
from midman.config import Config
from midman.forward import send_to
from midman.request import HttpRequest
from midman.response import HttpResponse


class RequestHandler(SimpleHTTPRequestHandler):
    transformers: List[Callable[[HttpRequest], HttpRequest]]
    request_cache: RequestCache

    def handle_request(self):
        with log_error():
            with wrap_context('handling request'):
                self.connection.settimeout(10)
                incoming_request = self.incoming_request()
                incoming_request.log_incoming()
                response = self.generate_response(incoming_request)
                self.respond_to_client(response)

    def incoming_request(self) -> HttpRequest:
        headers_dict = {parsed_line[0]: parsed_line[1] for parsed_line in self.headers.items()}
        method = self.command.lower()
        content_len = int(headers_dict.get('Content-Length', 0))
        content: bytes = self.rfile.read(content_len) if content_len else b''
        return HttpRequest(requestline=self.requestline, method=method, path=self.path,
                           headers=headers_dict,
                           content=content, client_addr=self.client_address[0],
                           client_port=self.client_address[1],
                           timestamp=now_seconds())

    def generate_response(self, incoming_request: HttpRequest) -> HttpResponse:
        for transformer in self.transformers:
            incoming_request = transformer(incoming_request)

        request_hash = hash(incoming_request)

        if Config.replay_clear_cache:
            self.request_cache.clear_old_cache()

        if self.request_cache.exists(request_hash) and Config.replay:
            return self.request_cache.replay_response(request_hash).log('> returning')

        response: HttpResponse = send_to(incoming_request, base_url=f'{Config.dst_url}').log('<< received')
        log.debug('> forwarding response back to client',
                  addr=incoming_request.client_addr, port=incoming_request.client_port)

        if Config.record or Config.replay:
            self.request_cache.save_response(incoming_request, request_hash, response)

        return response

    def respond_to_client(self, response: HttpResponse):
        self.send_response_only(response.status_code)

        if 'Content-Encoding' in response.headers:
            del response.headers['Content-Encoding']
            log.debug('removing Content-Encoding header')

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
            log.debug(f'dev variable set', name=var_name, value=var_value)
        var_value = getattr(sys.modules[__name__], var_name)
        self.respond_json({'name': var_name, 'value': var_value})
        return True


def chunks(lst: Sequence, n: int) -> Iterable:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
