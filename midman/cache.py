import json
import os
import zlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, List, Any

from dataclasses import dataclass, is_dataclass, asdict
from nuclear.sublog import log

from midman.config import Config
from midman.extension import Extensions
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
    def __init__(self, extensions: Extensions):
        self.extensions: Extensions = extensions
        self.cache: Dict[int, CacheEntry] = self._init_request_cache()

    def _init_request_cache(self) -> Dict[int, CacheEntry]:
        if Config.record_file and os.path.isfile(Config.record_file):
            txt = Path(Config.record_file).read_text()
            entries = json.loads(txt)
            loaded_cache = {}
            for entry in entries:
                parsed_entry = CacheEntry.from_json(entry)
                request_hash = self.request_hash(parsed_entry.request)
                loaded_cache[request_hash] = parsed_entry
            log.debug(f'loaded request-response pairs', record_file=Config.record_file,
                      read_entries=len(entries), distinct_entries=len(loaded_cache))
            return loaded_cache
        return {}

    def exists(self, request: HttpRequest) -> bool:
        request_hash = self.request_hash(request)
        return request_hash in self.cache

    def get(self, request_hash: int) -> CacheEntry:
        return self.cache[request_hash]

    def replay_response(self, request: HttpRequest) -> HttpResponse:
        request_hash = self.request_hash(request)
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
        if to_remove:
            log.debug('cleared old cache entries', removed=len(to_remove))

    def save_response(self, request: HttpRequest, response: HttpResponse):
        request_hash = self.request_hash(request)
        if request_hash not in self.cache:
            self.cache[request_hash] = CacheEntry(request, response)
            if Config.record and Config.record_file:
                serializable = list(self.cache.values())
                txt = json.dumps(serializable, sort_keys=True, indent=4, cls=EnhancedJSONEncoder)
                Path(Config.record_file).write_text(txt)
            log.debug(f'+ new request-response recorded', hash=request_hash, total_entries=len(self.cache))

    def request_hash(self, request: HttpRequest) -> int:
        traits_str = str(self.request_traits(request))
        return zlib.adler32(traits_str.encode('utf-8'))

    def request_traits(self, request: HttpRequest) -> Tuple:
        if self.extensions.request_traits_extractor is None:
            return default_request_traits(request)
        return self.extensions.request_traits_extractor(request)


def default_request_traits(request: HttpRequest) -> Tuple:
    return request.method, request.path, request.content, sorted_dict_trait(request.headers)


def sorted_dict_trait(d: Dict[str, Any]) -> List[Tuple[str, Any]]:
    return list(sorted(d.items(), key=lambda t: t[0]))


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
