from importlib.machinery import SourceFileLoader
from typing import Callable, Tuple, Optional

from dataclasses import dataclass, fields
from nuclear.sublog import log

from .config import Config
from .request import HttpRequest
from .response import HttpResponse


@dataclass
class Extensions(object):
    transform_request: Optional[Callable[[HttpRequest], HttpRequest]] = None
    transform_response: Optional[Callable[[HttpRequest, HttpResponse], HttpResponse]] = None
    can_be_cached: Optional[Callable[[HttpRequest], bool]] = None
    cache_request_traits: Optional[Callable[[HttpRequest], Tuple]] = None
    override_config: Optional[Callable[[Config], None]] = None


def load_extensions(extension_path: str) -> Extensions:
    if not extension_path:
        return Extensions()

    log.debug(f'loading extensions', path=extension_path)
    ext = Extensions()
    ext_module = SourceFileLoader("xman.transformer", extension_path).load_module()
    ext_names = [field.name for field in fields(Extensions)]
    for ext_name in ext_names:
        if hasattr(ext_module, ext_name):
            ext_value = getattr(ext_module, ext_name)
            if ext_value:
                setattr(ext, ext_name, ext_value)
                log.debug(f'loaded {ext_name} extension')

    return ext
