from nuclear import CliBuilder, parameter, argument, flag
from nuclear.types.boolean import boolean

from .setup import setup_proxy
from .version import __version__


def main():
    CliBuilder('xman', run=setup_proxy, help_on_empty=True, version=__version__,
               help='HTTP proxy recording & replaying requests').has(
        argument('dst_url', help='destination base url', required=False, default='http://127.0.0.1:8000'),
        parameter('listen_port', help='listen port for incoming requests', type=int, default=8080),
        parameter('listen_ssl', help='enable https on listening side', type=boolean, default=True),
        parameter('record', help='enable recording requests & responses', type=boolean, default=False),
        parameter('record_file', help='filename with recorded requests', default='tape.json'),
        parameter('replay', help='return cached results if found', type=boolean, default=False),
        parameter('replay_throttle', type=boolean, default=False,
                  help='throttle response if too many requests are made'),
        parameter('replay_clear_cache', help='enable clearing cache periodically', type=boolean, default=False),
        parameter('replay_clear_cache_seconds', help='clearing cache interval in seconds', type=int, default=1 * 60),
        parameter('allow_chunking', help='enable sending response in chunks', type=boolean, default=True),
        parameter('ext', help='load extensions from Python file'),
        flag('verbose', 'v', help='show more details in output'),
    ).run()
