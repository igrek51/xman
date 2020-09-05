import ssl
from socketserver import TCPServer

from nuclear.sublog import logerr, wrap_context, log

from .cache import RequestCache
from .config import Config
from .extension import load_extensions
from .handler import RequestHandler


def setup_proxy(listen_port: int, listen_ssl: bool, dst_url: str, record: bool, record_file: str, replay: bool,
                replay_throttle: bool, replay_clear_cache: bool, replay_clear_cache_seconds: int, allow_chunking: bool,
                ext: str, verbose: bool):
    with logerr():
        with wrap_context('initialization'):
            extensions = load_extensions(ext)
            config = Config(
                listen_port=listen_port,
                listen_ssl=listen_ssl,
                dst_url=dst_url,
                record=record,
                record_file=record_file,
                replay=replay,
                replay_throttle=replay_throttle,
                replay_clear_cache=replay_clear_cache,
                replay_clear_cache_seconds=replay_clear_cache_seconds,
                allow_chunking=allow_chunking,
                verbose=verbose,
            )
            if extensions.override_config:
                extensions.override_config(config)

            RequestHandler.extensions = extensions
            RequestHandler.config = config
            RequestHandler.cache = RequestCache(extensions, config)

            TCPServer.allow_reuse_address = True
            httpd = TCPServer(("", config.listen_port), RequestHandler)
            if config.listen_ssl:
                httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./dev-cert.pem', server_side=True)
            scheme = 'HTTPS' if config.listen_ssl else 'HTTP'
            log.info(f'Listening on {scheme} port {config.listen_port}...')
            try:
                httpd.serve_forever()
            finally:
                httpd.server_close()
