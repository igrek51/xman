from nuclear import CliBuilder, parameter, argument

from .setup import setup_proxy
from .version import __version__


def main():
    CliBuilder('middleman', run=setup_proxy, help_on_empty=True, version=__version__,
               help='HTTP proxy recording & replaying requests').has(
        argument('dst_url', help='destination base url', required=False, default='http://127.0.0.1:8000'),
        parameter('listen_port', help='listen port for incoming requests', type=int, default=8080),
        parameter('listen_ssl', help='enable https on listening side', type=int, default=0),
        parameter('record', help='enable recording requests & responses', type=int, default=0),
        parameter('record_file', help='filename with recorded requests', default='tape.json'),
        parameter('replay', help='return cached results if found', type=int, default=0),
        parameter('replay_throttle', help='throttle response if too many requests are made', type=int, default=0),
        parameter('replay_clear_cache', help='enable clearing cache periodically', type=int, default=1),
        parameter('replay_clear_cache_seconds', help='clearing cache interval in seconds', type=int, default=1 * 60),
        parameter('allow_chunking', help='enable sending response in chunks', type=int, default=1),
    ).run()
