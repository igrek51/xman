import ssl
from socketserver import TCPServer

from dataclasses import asdict
from nuclear.sublog import logerr, wrap_context, log

from .cache import RequestCache
from .config import Config
from .extension import load_extensions
from .handler import RequestHandler


def setup_proxy(listen_port: int, listen_ssl: bool, dst_url: str, record: bool, record_file: str, replay: bool,
                replay_throttle: bool, replay_clear_cache: bool, replay_clear_cache_seconds: int,
                config: str, verbose: int):
    with logerr():
        with wrap_context('initialization'):
            extensions = load_extensions(config)
            _config = Config(
                listen_port=listen_port,
                listen_ssl=listen_ssl,
                dst_url=dst_url,
                record=record,
                record_file=record_file,
                replay=replay,
                replay_throttle=replay_throttle,
                replay_clear_cache=replay_clear_cache,
                replay_clear_cache_seconds=replay_clear_cache_seconds,
                verbose=verbose,
            )
            if extensions.override_config:
                extensions.override_config(_config)
            log.info('Configuration set', **asdict(_config))

            RequestHandler.extensions = extensions
            RequestHandler.config = _config
            RequestHandler.cache = RequestCache(extensions, _config)

            TCPServer.allow_reuse_address = True
            httpd = TCPServer((_config.listen_addr, _config.listen_port), RequestHandler)
            if _config.listen_ssl:
                httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./dev-cert.pem', server_side=True)
            log.info(f'Listening on {_config.listen_scheme} port {_config.listen_port}...')
            try:
                httpd.serve_forever()
            finally:
                httpd.server_close()
