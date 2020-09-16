# Xman
[![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/igrek51/xman?label=github)](https://github.com/igrek51/xman)
[![PyPI](https://img.shields.io/pypi/v/x-man)](https://pypi.org/project/x-man)
[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/igrek5151/xman?label=docker)](https://hub.docker.com/r/igrek5151/xman)

`Xman` is a HTTP proxy recording & replaying requests.  
It acts as an extensible "Man in the middle" server, which can:  
- forward requests to other address
- return cached results immediately without need to proxying
- record incoming requests to a file, restore responses from there
- transform requests & responses on the fly (eg. replace path with regex)
- throttle requests when clients are making them too frequently

With `xman` you can setup a mock server imitating a real server:  
1. Configure it to forward to a real server. Enable recording requests and replaying responses.
2. Make some typical requests. Request-response entries will be recorded to a file.
3. You can turn off a real server now. Responses are returned from cache.
4. Use `xman` with recorded data to setup lighweight HTTP service mocks anywhere.

# Installation
```shell
pip3 install x-man
```

Python 3.6 (or newer) is required.

# Quickstart
Configure listening on SSL port 8443, forwarding requests to https://127.0.0.1:8000 with caching.
When the same request comes, cached response will be returned. 
```console
$ xman https://127.0.0.1:8000 --listen-port 8443 --listen-ssl=true --replay=true
[2020-09-05 19:39:55] [INFO ] CACHE: loaded request-response pairs record_file=tape.json loaded=17 conflicts=0
[2020-09-05 19:39:55] [INFO ] Listening on HTTPS port 8443... ssl=True addr= port=8443 destination=https://127.0.0.1:8000
```

# Run in docker
You can run `xman` in docker and pass your custom arguments at the end.  
That command just prints out the help:
```bash
docker run --rm -it --network=host igrek5151/xman:latest
```
Basic forwarding all requests with rudimentary caching:
```bash
docker run --rm -it --network=host igrek5151/xman:latest \
  http://127.0.0.1:8000 --listen-port 8443 --listen-ssl=true --replay=true
```

For more customization create your own `extensions.py` extension file (example in section below) and run:
```bash
docker run --rm -it --network=host -v `pwd`/extensions.py:/extensions.py igrek5151/xman:latest \
  --config=/extensions.py
```
If you want to keep recorded requests & responses outside container, mount `tape.json` as well:
```bash
touch tape.json
docker run --rm -it --network=host -v `pwd`/extensions.py:/extensions.py -v `pwd`/tape.json:/src/tape.json igrek5151/xman:latest \
  --config=/extensions.py --record=true --replay=true
```

# Extensions
If you need more customization, you can specify extension file, where you can implement your custom behaviour or even processing logic.
In order to do that you must create Python script and pass its filename by parameter: `xman --config extensions.py`.

In extension file you can specify request / response mappers or custom comparator deciding which requests should be treated as the same. Using that you can achieve custom behaviour for some particular type of requests.

Implement your function in place of one of the following functions:
- `transform_request(request: HttpRequest) -> HttpRequest` - Transforms each incoming Request before further processing (caching, forwarding).
- `transform_response(request: HttpRequest, response: HttpResponse) -> HttpResponse` - Transforms each Response before sending it.
- `immediate_responder(request: HttpRequest) -> Optional[HttpResponse]` - Returns immediate response for matched request instead of proxying it further or searching in cache
- `can_be_cached(request: HttpRequest, response: HttpResponse) -> bool` - Indicates whether particular request with response could be saved in cache.
- `cache_request_traits(request: HttpRequest) -> Tuple` - Gets tuple denoting request uniqueness. Requests with same results are treated as the same when caching.
- `override_config(config: Config)` - Overrides default parameters in config.

## Extensions example
**extensions.py**
```python
import re
from typing import Tuple, Optional

from nuclear.sublog import log

from xman.cache import sorted_dict_trait
from xman.config import Config
from xman.request import HttpRequest
from xman.response import HttpResponse


def transform_request(request: HttpRequest) -> HttpRequest:
    """Transforms each incoming Request before further processing (caching, forwarding)."""
    match = re.match(r'^/some/path/(.+?)(/[a-z]+)(/.*)', request.path)
    if match:
        request.path = match.expand(r'\3')
        log.debug('request path transformed', path=request.path)
    return request


def immediate_responder(request: HttpRequest) -> Optional[HttpResponse]:
    """Returns immediate response for matched request instead of proxying it further or searching in cache"""
    if request.path.startswith('/some/api'):
        return HttpResponse(status_code=200, headers={'Content-Type': 'application/json'}, content=''.encode())
    return None


def transform_response(request: HttpRequest, response: HttpResponse) -> HttpResponse:
    """Transforms each Response before sending it."""
    if request.path.startswith('/some/api'):
        log.debug('Found Ya', path=request.path)
        response = response.set_content('{"payload": "anythingyouwish"}"')
    return response


def can_be_cached(request: HttpRequest, response: HttpResponse) -> bool:
    """Indicates whether particular request with response could be saved in cache."""
    return response.status_code == 200


def cache_request_traits(request: HttpRequest) -> Tuple:
    """Gets tuple denoting request uniqueness. Requests with same results are treated as the same when caching."""
    if request.path.endswith('/some/path'):
        return request.method, request.path, sorted_dict_trait(request.headers)
    return request.method, request.path, request.content


def override_config(config: Config):
    """Overrides default parameters in config."""
    # config.listen_port = 8080
    # config.listen_ssl = True
    # config.dst_url = 'http://127.0.0.1:8000'
    # config.record = False
    # config.record_file = 'tape.json'
    # config.replay = False
    # config.replay_throttle = False
    # config.replay_clear_cache = False
    # config.replay_clear_cache_seconds = 60
    # config.allow_chunking = True
    # config.proxy_timeout = 10
    config.verbose = 0

```

# Usage
See help by typing `xman`:
```console
xman v0.1.2 (nuclear v1.1.9) - HTTP proxy recording & replaying requests

Usage:
xman [OPTIONS] [DST_URL]

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
  --config CONFIG                                         - load extensions from Python file
  -v, --verbose                                           - show more details in output

```
