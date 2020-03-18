from nuclear import CliBuilder, parameter, flag, argument

from .midman import setup_proxy
from .version import __version__


def main():
    CliBuilder('middleman', run=setup_proxy, help_on_empty=True, version=__version__,
               help='HTTP proxy recording & replaying requests').has(
        parameter('listen_port', help='listen port for incoming requests', type=int, default=8080),
        flag('listen_ssl', help='enable https on listening side'),
        argument('dst_url', help='destination base url', required=False, default='http://127.0.0.1:8000'),
        flag('record', help='enable recording requests & responses'),
        parameter('record_file', help='filename with recorded requests', default='tape.json'),
    ).run()
