import ssl
from socketserver import TCPServer

from nuclear.sublog import log_error, wrap_context, log

from midman.cache import RequestCache
from midman.config import Config
from midman.handler import RequestHandler
from midman.transformer import transformers


def setup_proxy(listen_port: int, listen_ssl: int, dst_url: str, record: bool, record_file: str, replay: int,
                replay_throttle: int, replay_clear_cache: int, replay_clear_cache_seconds: int, allow_chunking: int):
    with log_error():
        with wrap_context('initialization'):
            Config.dst_url = dst_url
            Config.record = record
            Config.record_file = record_file
            Config.replay = replay
            Config.replay_throttle = replay_throttle
            Config.replay_clear_cache = replay_clear_cache
            Config.replay_clear_cache_seconds = replay_clear_cache_seconds
            Config.allow_chunking = allow_chunking

            RequestHandler.request_cache = RequestCache()
            RequestHandler.transformers = transformers
            TCPServer.allow_reuse_address = True
            httpd = TCPServer(("", listen_port), RequestHandler)
            if listen_ssl:
                httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./dev-cert.pem', server_side=True)
            scheme = 'HTTPS' if listen_ssl else 'HTTP'
            log.info(f'Listening on {scheme} port {listen_port}...')
            try:
                httpd.serve_forever()
            finally:
                httpd.server_close()
