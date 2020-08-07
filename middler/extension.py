from typing import Callable, List, Tuple, Optional
from importlib.machinery import SourceFileLoader

from dataclasses import dataclass, field
from nuclear.sublog import log

from middler.config import Config
from middler.request import HttpRequest
from middler.response import HttpResponse


@dataclass
class Extensions(object):
    request_transformers: List[Callable[[HttpRequest], HttpRequest]] = field(default_factory=lambda: [])
    response_transformers: List[Callable[[HttpResponse], HttpResponse]] = field(default_factory=lambda: [])
    cache_traits_extractor: Optional[Callable[[HttpRequest], Tuple]] = None
    cache_predicate: Optional[Callable[[HttpRequest], bool]] = None
    config_builder: Optional[Callable[[...], Config]] = None


def load_extensions(extension_path: str) -> Extensions:
    if not extension_path:
        return Extensions()

    log.debug(f'loading extensions', path=extension_path)
    extensions = Extensions()
    ext_module = SourceFileLoader("middler.transformer", extension_path).load_module()

    if hasattr(ext_module, 'request_transformers'):
        request_transformers = ext_module.request_transformers
        extensions.request_transformers = request_transformers
        names = ','.join([t.__name__ for t in request_transformers])
        log.debug(f'loaded request_transformers', count=len(request_transformers), names=names)

    if hasattr(ext_module, 'response_transformers'):
        response_transformers = ext_module.response_transformers
        extensions.response_transformers = response_transformers
        names = ','.join([t.__name__ for t in response_transformers])
        log.debug(f'loaded response_transformers', count=len(response_transformers), names=names)

    if hasattr(ext_module, 'cache_traits_extractor'):
        cache_traits_extractor = ext_module.cache_traits_extractor
        extensions.cache_traits_extractor = cache_traits_extractor
        log.debug(f'loaded cache_traits_extractor', name=cache_traits_extractor.__name__)

    if hasattr(ext_module, 'cache_predicate'):
        cache_predicate = ext_module.cache_predicate
        extensions.cache_predicate = cache_predicate
        log.debug(f'loaded cache_predicate', name=cache_predicate.__name__)

    if hasattr(ext_module, 'config_builder'):
        config_builder = ext_module.config_builder
        extensions.config_builder = config_builder
        log.debug(f'loaded config_builder', name=config_builder.__name__)

    return extensions
