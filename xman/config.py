from dataclasses import dataclass


@dataclass
class Config(object):
    listen_port: int
    listen_ssl: bool
    dst_url: str
    record: bool
    record_file: str
    replay: bool
    replay_throttle: bool
    replay_clear_cache: bool
    replay_clear_cache_seconds: int
    # Verbosity level: 0 (disabled), 1 or 2 (highest)
    verbose: int
    allow_chunking: bool = True
    timeout: int = 10
    listen_addr: str = ''
