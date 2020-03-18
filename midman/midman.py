import json
import os
import re
import ssl
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from typing import Dict, Iterable, Sequence, Tuple, Callable

import requests
import urllib3
from dataclasses import dataclass, is_dataclass, asdict
from nuclear.sublog import log, log_error, wrap_context

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

record = False
record_file = 'tape.json'

replay = False
replay_throttle = True
replay_clear_cache = True
replay_clear_cache_seconds = 1 * 60

allow_chunking = True


@dataclass
class HttpRequest(object):
    requestline: str
    method: str
    path: str
    headers: Dict[str, str]
    content: bytes
    client_addr: str
    client_port: int
    timestamp: float

    def traits(self) -> Tuple:
        return self.method, self.path, self.content, str(self.headers)

    def show(self, prefix: str):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'\n{prefix} [{current_time}] {self.requestline} {self.headers}')
        if self.content:
            decoded: str = self.content.decode('utf-8')
            print(f'{prefix} {decoded}')

    def __hash__(self):
        return hash(self.traits())

    def __eq__(self, other):
        return self.traits() == other.traits()

    @staticmethod
    def from_json(data: dict) -> 'HttpRequest':
        data['content'] = data.get('content').encode('utf-8')
        return HttpRequest(**data)


@dataclass
class HttpResponse(object):
    status_code: int
    headers: Dict[str, str]
    content: bytes

    def show(self, prefix: str) -> 'HttpResponse':
        print(prefix, self.status_code, self.headers)
        print(prefix, self.content.decode('utf-8'))
        return self

    @staticmethod
    def from_json(data: dict) -> 'HttpResponse':
        data['content'] = data.get('content').encode('utf-8')
        return HttpResponse(**data)


@dataclass
class CacheEntry(object):
    request: HttpRequest
    response: HttpResponse

    @staticmethod
    def from_json(data: dict) -> 'CacheEntry':
        return CacheEntry(
            request=HttpRequest.from_json(data.get('request')),
            response=HttpResponse.from_json(data.get('response')),
        )


def transformer_cutpath(request: HttpRequest) -> HttpRequest:
    if request.path.startswith('/proxy/'):
        match = re.search(r'^/proxy/(.+?)(/[a-z]+)(/.*)', request.path)
        if match:
            request.path = match.group(3)
    return request


transformers = [
    transformer_cutpath
]


def setup_proxy(listen_port: int, listen_ssl: bool, dst_url: str, record: bool, record_file: str):
    with log_error():
        TCPServer.allow_reuse_address = True
        RequestHandler.dst_url = dst_url
        RequestHandler.transformers = transformers

        httpd = TCPServer(("", listen_port), RequestHandler)
        if listen_ssl:
            httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./dev-cert.pem', server_side=True)
        scheme = 'HTTPS' if listen_ssl else 'HTTP'
        print(f'Listening on {scheme} port {listen_port}...')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return super().default(obj)


def send_to(request: HttpRequest, base_url: str) -> HttpResponse:
    url = f'{base_url}{request.path}'
    print(f'>> proxying to {url}')
    response = requests.request(request.method, url, verify=False, allow_redirects=True, stream=False,
                                timeout=10, headers=request.headers, data=request.content)
    content: bytes = response.content
    return HttpResponse(status_code=response.status_code, headers=dict(response.headers), content=content)


def init_request_cache() -> Dict[int, CacheEntry]:
    if record_file and os.path.isfile(record_file):
        with open(record_file, 'r') as f:
            print(f'loading initial cache from {record_file}...')
            entries = json.load(f)
            loaded_cache = {}
            for entry in entries:
                parsed_entry = CacheEntry.from_json(entry)
                request_hash = hash(parsed_entry.request)
                loaded_cache[request_hash] = parsed_entry
            print(f'loaded {len(loaded_cache)} request-response pairs')
            return loaded_cache
    return {}


def clear_old_cache():
    to_remove = []
    now_timestamp = now_seconds()
    for request_hash, entry in request_cache.items():
        if now_timestamp - entry.request.timestamp > replay_clear_cache_seconds:
            to_remove.append(request_hash)
    for request_hash in to_remove:
        del request_cache[request_hash]


request_cache: Dict[int, CacheEntry] = init_request_cache()
too_many_requests_response = HttpResponse(status_code=429, headers={}, content=b'')


class RequestHandler(SimpleHTTPRequestHandler):
    dst_url: str
    transformers: Callable[[HttpRequest], HttpRequest]

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

        if replay_clear_cache:
            clear_old_cache()

        if request_hash in request_cache and replay:
            if replay_throttle:
                print(f'> Sending throttled response, hash: #{request_hash}')
                return too_many_requests_response.show('>')
            print(f'> Sending cached response, hash: #{request_hash}')
            cached = request_cache[request_hash]
            return cached.response.show('>')

        response: HttpResponse = send_to(incoming_request, base_url=f'{self.dst_url}').show('<<')
        print(f'> forwarding response back to client {incoming_request.client_addr}:{incoming_request.client_port}')

        if record or replay:
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

        if allow_chunking and response.headers.get('Transfer-Encoding') == 'chunked':
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

    @staticmethod
    def save_response(incoming_request: HttpRequest, request_hash: int, response: HttpResponse):
        if request_hash not in request_cache:
            request_cache[request_hash] = CacheEntry(incoming_request, response)
            if record and record_file:
                with open(record_file, 'w') as f:
                    serializable = list(request_cache.values())
                    json.dump(serializable, f, sort_keys=True, indent=4, cls=EnhancedJSONEncoder)
            print(f'+ new request-response recorded, hash: #{request_hash} [{len(request_cache)} entries in total]')

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


def chunks(lst: Sequence, n: int) -> Iterable:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def now_seconds() -> float:
    return datetime.now().timestamp()
