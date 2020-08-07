from typing import Callable, List, Tuple, Optional
from importlib.machinery import SourceFileLoader

from dataclasses import dataclass, field
from nuclear.sublog import log
from middler.request import HttpRequest


@dataclass
class Extensions(object):
    transformers: List[Callable[[HttpRequest], HttpRequest]] = field(default_factory=lambda: [])
    request_traits_extractor: Optional[Callable[[HttpRequest], Tuple]] = None


def load_extensions(extension_path: str) -> Extensions:
    if not extension_path:
        return Extensions()

    log.debug(f'loading extensions', path=extension_path)
    extensions = Extensions()
    ext_module = SourceFileLoader("middler.transformer", extension_path).load_module()

    if hasattr(ext_module, 'transformers'):
        transformers = ext_module.transformers
        extensions.transformers = transformers
        names = ','.join([t.__name__ for t in transformers])
        log.debug(f'loaded transformers', count=len(transformers), names=names)

    if hasattr(ext_module, 'request_traits_extractor'):
        request_traits_extractor = ext_module.request_traits_extractor
        extensions.request_traits_extractor = request_traits_extractor
        log.debug(f'loaded request_traits_extractor', name=request_traits_extractor.__name__)

    return extensions
