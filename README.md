# middler
[![GitHub version](https://badge.fury.io/gh/igrek51%2Fmiddler.svg)](https://github.com/igrek51/middler)
[![PyPI version](https://badge.fury.io/py/middler.svg)](https://pypi.org/project/middler)

middler is a HTTP proxy recording & replaying requests. It can:  
- forward requests to other address
- return cached results immediately without need to proxying
- record incoming requests to a file, restore responses from there
- throttle requests when clients are making them too frequently
- transform requests on the fly (eg. replace path with regex)

With `middler` you can setup a mock server imitating real server:  
1. Configure forwarding to real server. Enable recording requests and replaying responses,
2. Make some typical requests. Request-response entries will be recorded to a file.
3. You can turn off real server. Responses are returned from cache.

# Installation
```shell
pip3 install middler
```

Python 3.6 (or newer) is required.

# Usage
See help by typing `middler`:
```console
middler v0.1.1 (nuclear v1.1.7) - HTTP proxy recording & replaying requests

Usage:
middler [OPTIONS] [DST_URL]

Arguments:
   [DST_URL] - destination base url
               Default: http://127.0.0.1:8000

Options:
  --version                                               - Print version information and exit
  -h, --help [SUBCOMMANDS...]                             - Display this help and exit
  --listen-port LISTEN_PORT                               - listen port for incoming requests
                                                            Default: 8080
  --listen-ssl LISTEN_SSL                                 - enable https on listening side
                                                            Default: True
  --record RECORD                                         - enable recording requests & responses
                                                            Default: False
  --record-file RECORD_FILE                               - filename with recorded requests
                                                            Default: tape.json
  --replay REPLAY                                         - return cached results if found
                                                            Default: False
  --replay-throttle REPLAY_THROTTLE                       - throttle response if too many requests are made
                                                            Default: False
  --replay-clear-cache REPLAY_CLEAR_CACHE                 - enable clearing cache periodically
                                                            Default: False
  --replay-clear-cache-seconds REPLAY_CLEAR_CACHE_SECONDS - clearing cache interval in seconds
                                                            Default: 60
  --allow-chunking ALLOW_CHUNKING                         - enable sending response in chunks
                                                            Default: True
  --ext EXT                                               - load extensions from Python file

```

Listne on SSL port 8443, forward requests to http://127.0.0.1:8000 with default caching.
When same request comes, cached response will be returned. 
```console
$ middler http://127.0.0.1:8000 --listen-port 8443 --listen-ssl=true --replay=true
[2020-07-29 18:19:58] [DEBUG] loaded request-response pairs record_file=tape.json read_entries=2 distinct_entries=1
[2020-07-29 18:19:58] [INFO ] Listening on HTTPS port 8443...
```

# Extensions
If you need more customization, you can specify extension file, where you can implement your custom behaviour.
In order to do that you must create Python script and pass it by parameter `--ext ext.py`.

In extension file you can define custom comparator deciding which requests should be treated as the same.
Assign your function to `request_traits_extractor: Callable[[HttpRequest], Tuple]` variable in given extension file.

Custom rules for transforming requests may be assigned to `transformers: List[Callable[[HttpRequest], HttpRequest]]` variable.

## Extensions example
**ext.py**
```python
import re
from typing import List, Callable, Tuple

from nuclear.sublog import log

from middler.request import HttpRequest


def _transformer_shorten_path(request: HttpRequest) -> HttpRequest:
    if request.path.startswith('/path/'):
        match = re.search(r'^/path/(.+?)(/[a-z]+)(/.*)', request.path)
        if match:
            request.path = match.group(3)
            log.debug('request path transformed', path=request.path)
    return request


transformers: List[Callable[[HttpRequest], HttpRequest]] = [
    _transformer_shorten_path,
]


def _default_request_traits(request: HttpRequest) -> Tuple:
    return request.method, request.path, request.content, sorted(request.headers.items(), key=lambda t: t[0])


request_traits_extractor: Callable[[HttpRequest], Tuple] = _default_request_traits
```
