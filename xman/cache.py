import json
import os
import zlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, List, Any

from dataclasses import dataclass, is_dataclass, asdict
from nuclear.sublog import log

from .config import Config
from .extension import Extensions
from .request import HttpRequest
from .response import HttpResponse


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
    def __init__(self, extensions: Extensions, config: Config):
        self.extensions: Extensions = extensions
        self.config: Config = config
        self.cache: Dict[int, CacheEntry] = self._init_request_cache()

    def _init_request_cache(self) -> Dict[int, CacheEntry]:
        if self.config.record_file and os.path.isfile(self.config.record_file):
            txt = Path(self.config.record_file).read_text()
            if not txt:
                return {}
            entries = json.loads(txt)
            loaded_cache = {}
            for entry in entries:
                parsed_entry = CacheEntry.from_json(entry)
                request_hash = self._request_hash(parsed_entry.request)
                loaded_cache[request_hash] = parsed_entry
            log.debug(f'CACHE: loaded request-response pairs', record_file=self.config.record_file,
                      read_entries=len(entries), distinct_entries=len(loaded_cache))
            return loaded_cache
        return {}

    def has_cached_response(self, request: HttpRequest) -> bool:
        return self.config.replay and self._can_be_cached(request) and self._request_hash(request) in self.cache

    def _can_be_cached(self, request: HttpRequest) -> bool:
        if self.extensions.can_be_cached is None:
            return True
        return self.extensions.can_be_cached(request)

    def get(self, request_hash: int) -> CacheEntry:
        return self.cache[request_hash]

    def replay_response(self, request: HttpRequest) -> HttpResponse:
        request_hash = self._request_hash(request)
        if self.config.replay_throttle:
            log.debug('CACHE: Throttled response', hash=request_hash)
            return too_many_requests_response
        log.debug('CACHE: Found cached response', hash=request_hash)
        return self.cache[request_hash].response

    def clear_old(self):
        if not self.config.replay_clear_cache:
            return
        to_remove = []
        now_timestamp: float = now_seconds()
        for request_hash, entry in self.cache.items():
            if now_timestamp - entry.request.timestamp > self.config.replay_clear_cache_seconds:
                to_remove.append(request_hash)
        for request_hash in to_remove:
            del self.cache[request_hash]
        if to_remove:
            log.debug('CACHE: cleared old cache entries', removed=len(to_remove))

    def saving_enabled(self, request: HttpRequest) -> bool:
        return (self.config.record or self.config.replay) and self._can_be_cached(request)

    def save_response(self, request: HttpRequest, response: HttpResponse):
        request_hash = self._request_hash(request)
        if request_hash not in self.cache:
            self.cache[request_hash] = CacheEntry(request, response)
            if self.config.record and self.config.record_file:
                serializable = list(self.cache.values())
                txt = json.dumps(serializable, sort_keys=True, indent=4, cls=EnhancedJSONEncoder)
                Path(self.config.record_file).write_text(txt)
            log.debug(f'+ CACHE: new request-response recorded', hash=request_hash, total_entries=len(self.cache))

    def _request_hash(self, request: HttpRequest) -> int:
        traits_str = str(self._request_traits(request))
        return zlib.adler32(traits_str.encode())

    def _request_traits(self, request: HttpRequest) -> Tuple:
        if self.extensions.cache_request_traits is None:
            return default_request_traits(request)
        return self.extensions.cache_request_traits(request)


def default_request_traits(request: HttpRequest) -> Tuple:
    return request.method, request.path, request.content, sorted_dict_trait(request.headers)


def sorted_dict_trait(d: Dict[str, Any]) -> List[Tuple[str, Any]]:
    return sorted([(k, v) for k, v in d.items()], key=lambda t: t[0])


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
