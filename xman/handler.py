from http.server import SimpleHTTPRequestHandler
from typing import Optional

from nuclear.sublog import log, wrap_context, logerr

from xman.chunk import send_chunked_response
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
        with logerr('handling request'):
            self.connection.settimeout(self.config.timeout)
            incoming_request = self.incoming_request()
            incoming_request.log(self.config.verbose)
            response_0 = self.generate_response(incoming_request)
            response = response_0.transform(self.extensions.transform_response, incoming_request)
            if response != response_0 and self.config.verbose >= 2:
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
            if request != request_0 and self.config.verbose >= 2:
                log.debug('request transformed')

            immediate_reponse = self.find_immediate_response(request)
            if immediate_reponse:
                return immediate_reponse.log('> immediate response', self.config.verbose)

            self.cache.clear_old()
            if self.cache.has_cached_response(request):
                return self.cache.replay_response(request).log('> Cache: returning cached response',
                                                               self.config.verbose)

            if self.config.replay and self.config.verbose:
                log.warn('request not found in cache', path=request.path)
            response: HttpResponse = proxy_request(request, default_url=self.config.dst_url,
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
        with wrap_context('responding to client'):
            self.send_response_only(response.status_code)

            if has_header(response.headers, 'Content-Encoding'):
                del response.headers['Content-Encoding']
                if self.config.verbose >= 2:
                    log.debug('removing Content-Encoding header')

            if not has_header(response.headers, 'Content-Length') and \
                    not has_header(response.headers, 'Transfer-Encoding') and response.content:
                response.headers['Content-Length'] = str(len(response.content))
                log.warn('adding missing Content-Length header')

            if has_header(response.headers, 'Content-Length') and has_header(response.headers, 'Transfer-Encoding'):
                del response.headers['Content-Length']
                log.warn('removed Content-Length header conflicting with Transfer-Encoding')

            for name, value in response.headers.items():
                self.send_header(name, value)
            self.end_headers()

            if self.config.allow_chunking and response.headers.get('Transfer-Encoding') == 'chunked':
                send_chunked_response(self.wfile, response.content)
            else:
                self.wfile.write(response.content)
            self.close_connection = True
            if self.config.verbose >= 2:
                log.debug('> response sent', client_addr=self.client_address[0], client_port=self.client_address[1])

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
