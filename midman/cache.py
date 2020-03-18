import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from dataclasses import dataclass, is_dataclass, asdict
from nuclear.sublog import log

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
        self.cache: Dict[int, CacheEntry] = self._init_request_cache()

    @staticmethod
    def _init_request_cache() -> Dict[int, CacheEntry]:
        if Config.record_file and os.path.isfile(Config.record_file):
            txt = Path(Config.record_file).read_text()
            entries = json.loads(txt)
            loaded_cache = {}
            for entry in entries:
                parsed_entry = CacheEntry.from_json(entry)
                request_hash = hash(parsed_entry.request)
                loaded_cache[request_hash] = parsed_entry
            log.debug(f'loaded request-response pairs', entries=len(loaded_cache), record_file=Config.record_file)
            return loaded_cache
        return {}

    def exists(self, request_hash: int) -> bool:
        return request_hash in self.cache

    def get(self, request_hash: int) -> CacheEntry:
        return self.cache[request_hash]

    def replay_response(self, request_hash: int) -> HttpResponse:
        if Config.replay_throttle:
            log.debug('> Throttled response', hash=request_hash)
            return too_many_requests_response
        log.debug('> Sending cached response', hash=request_hash)
        return self.cache[request_hash].response

    def clear_old_cache(self):
        to_remove = []
        now_timestamp: float = now_seconds()
        for request_hash, entry in self.cache.items():
            if now_timestamp - entry.request.timestamp > Config.replay_clear_cache_seconds:
                to_remove.append(request_hash)
        for request_hash in to_remove:
            del self.cache[request_hash]

    def save_response(self, incoming_request: HttpRequest, request_hash: int, response: HttpResponse):
        if request_hash not in self.cache:
            self.cache[request_hash] = CacheEntry(incoming_request, response)
            if Config.record and Config.record_file:
                serializable = list(self.cache.values())
                txt = json.dumps(serializable, sort_keys=True, indent=4, cls=EnhancedJSONEncoder)
                Path(Config.record_file).write_text(txt)
            log.debug(f'+ new request-response recorded', hash=request_hash, total_entries=len(self.cache))


too_many_requests_response = HttpResponse(status_code=429, headers={}, content=b'')


def now_seconds() -> float:
    return datetime.now().timestamp()


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return super().default(obj)
