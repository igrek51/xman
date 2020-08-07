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
    allow_chunking: bool
    verbose: bool
