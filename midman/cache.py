import json
import os
from datetime import datetime
from typing import Dict

from dataclasses import dataclass, is_dataclass, asdict

from midman.config import Config
from midman.request import HttpRequest
from midman.response import HttpResponse


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


class RequestCache(object):
    def __init__(self):
        self.cache = self._init_request_cache()

    def _init_request_cache(self) -> Dict[int, CacheEntry]:
        if Config.record_file and os.path.isfile(Config.record_file):
            with open(Config.record_file, 'r') as f:
                print(f'loading initial cache from {Config.record_file}...')
                entries = json.load(f)
                loaded_cache = {}
                for entry in entries:
                    parsed_entry = CacheEntry.from_json(entry)
                    request_hash = hash(parsed_entry.request)
                    loaded_cache[request_hash] = parsed_entry
                print(f'loaded {len(loaded_cache)} request-response pairs')
                return loaded_cache
        return {}

    def clear_old_cache(self):
        to_remove = []
        now_timestamp: float = now_seconds()
        for request_hash, entry in self.cache.items():
            if now_timestamp - entry.request.timestamp > Config.replay_clear_cache_seconds:
                to_remove.append(request_hash)
        for request_hash in to_remove:
            del self.cache[request_hash]


def now_seconds() -> float:
    return datetime.now().timestamp()


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return super().default(obj)
