from dataclasses import dataclass


@dataclass
class Config(object):
    listen_addr: str = ''
    listen_port: int = 8080
    listen_ssl: bool = True
    dst_url: str = 'http://127.0.0.1:8000'
    record: bool = False
    record_file: str = 'tape.json'
    replay: bool = False
    replay_throttle: bool = False
    replay_clear_cache: bool = False
    replay_clear_cache_seconds: int = 60
    timeout: int = 10
    # Verbosity level: 0 (disabled), 1 or 2 (highest)
    verbose: int = 0
    allow_chunking: bool = True

    @property
    def listen_scheme(self) -> str:
        return 'HTTPS' if self.listen_ssl else 'HTTP'
