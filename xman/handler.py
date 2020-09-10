import json
import sys
from http.server import SimpleHTTPRequestHandler
from typing import Dict, Iterable, Sequence, Optional

from nuclear.sublog import log, log_error, wrap_context

from xman.header import has_header, get_header
from .cache import RequestCache, now_seconds
from .config import Config
from .extension import Extensions
from .proxy import proxy_request
from .request import HttpRequest
from .response import HttpResponse


class RequestHandler(SimpleHTTPRequestHandler):
    extensions: Extensions
    config: Config
    cache: RequestCache

    def handle_request(self):
        with log_error():
            with wrap_context('handling request'):
                self.connection.settimeout(self.config.timeout)
                incoming_request = self.incoming_request()
                incoming_request.log(self.config.verbose)
                response_0 = self.generate_response(incoming_request)
                response = response_0.transform(self.extensions.transform_response, incoming_request)
                if response != response_0 and self.config.verbose:
                    response.log('response transformed', self.config.verbose)
                self.respond_to_client(response)

    def incoming_request(self) -> HttpRequest:
        with wrap_context('building incoming request'):
            headers_dict = {key: self.headers[key] for key in self.headers.keys()}
            method = self.command.upper()
            content_len = int(get_header(headers_dict, 'Content-Length', '0'))
            content: bytes = self.rfile.read(content_len) if content_len else b''
            return HttpRequest(requestline=self.requestline, method=method, path=self.path,
                               headers=headers_dict, content=content,
                               client_addr=self.client_address[0], client_port=self.client_address[1],
                               timestamp=now_seconds())

    def generate_response(self, request_0: HttpRequest) -> HttpResponse:
        with wrap_context('generating response'):
            request = request_0.transform(self.extensions.transform_request)
            if request != request_0 and self.config.verbose:
                log.debug('request transformed')

            quick_reponse = self.find_immediate_response(request)
            if quick_reponse:
                return quick_reponse.log('> immediate response', self.config.verbose)

            self.cache.clear_old()
            if self.cache.has_cached_response(request):
                return self.cache.replay_response(request).log('> returning', self.config.verbose)

            response: HttpResponse = proxy_request(request, base_url=self.config.dst_url,
                                                   timeout=self.config.timeout, verbose=self.config.verbose)
            response.log('<< received', self.config.verbose)

            if self.cache.saving_enabled(request, response):
                self.cache.save_response(request, response)

            return response

    def find_immediate_response(self, request: HttpRequest) -> Optional[HttpResponse]:
        if self.extensions.immediate_responder is None:
            return None
        return self.extensions.immediate_responder(request)

    def respond_to_client(self, response: HttpResponse):
        with wrap_context('responding back to client'):
            self.send_response_only(response.status_code)

            if has_header(response.headers, 'Content-Encoding'):
                del response.headers['Content-Encoding']
                if self.config.verbose:
                    log.debug('removing Content-Encoding header')

            if not has_header(response.headers, 'Content-Length') and \
                    not has_header(response.headers, 'Transfer-Encoding') and response.content:
                response.headers['Content-Length'] = str(len(response.content))
                log.warn('adding missing Content-Length header')

            for name, value in response.headers.items():
                self.send_header(name, value)
            self.end_headers()

            if self.config.allow_chunking and response.headers.get('Transfer-Encoding') == 'chunked':
                self.send_chunked_response(chunks(response.content, 512))
            else:
                self.wfile.write(response.content)
            self.close_connection = True
            if self.config.verbose >= 2:
                log.debug('> response sent', client_addr=self.client_address[0], client_port=self.client_address[1])

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
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def do_PUT(self):
        self.handle_request()

    def do_DELETE(self):
        self.handle_request()

    def do_HEAD(self):
        self.handle_request()


def chunks(lst: Sequence, n: int) -> Iterable:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
