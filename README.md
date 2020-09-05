# Xman
![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/igrek51/xman)
![PyPI](https://img.shields.io/pypi/v/x-man)
![Docker Image Version (latest by date)](https://img.shields.io/docker/v/igrek5151/xman)

`Xman` is a HTTP proxy recording & replaying requests.  
It acts as an extensible "Man in the middle" server, which can:  
- forward requests to other address
- return cached results immediately without need to proxying
- record incoming requests to a file, restore responses from there
- throttle requests when clients are making them too frequently
- transform requests & responses on the fly (eg. replace path with regex)

With `xman` you can setup a mock server imitating a real server:  
1. Configure forwarding to a real server. Enable recording requests and replaying responses,
2. Make some typical requests. Request-response entries will be recorded to a file.
3. You can turn off real server now. Responses are returned from cache.
4. Use it to setup lighweight HTTP service mock.

# Installation
```shell
pip3 install x-man
```

Python 3.6 (or newer) is required.

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
  --ext EXT                                               - load extensions from Python file
  -v, --verbose                                           - show more details in output

```

Listen on SSL port 8443, forward requests to http://127.0.0.1:8000 with caching.
When same request comes, cached response will be returned. 
```console
$ xman http://127.0.0.1:8000 --listen-port 8443 --listen-ssl=true --replay=true
[2020-07-29 18:19:58] [DEBUG] loaded request-response pairs record_file=tape.json read_entries=2 distinct_entries=1
[2020-07-29 18:19:58] [INFO ] Listening on HTTPS port 8443...
```

# Extensions
If you need more customization, you can specify extension file, where you can implement your custom behaviour.
In order to do that you must create Python script and pass its filename by parameter: `xman --ext ext.py`.

In extension file you can specify request / response mappers or custom comparator deciding which requests should be treated as the same. Using that you can achieve custom behaviour for some particular type of requests.

Implement your function in place of one of the following functions:
- `transform_request(request: HttpRequest) -> HttpRequest` - Transforms each incoming Request before further processing (caching, forwarding).
- `transform_response(request: HttpRequest, response: HttpResponse) -> HttpResponse` - Transforms each Response before sending it.
- `can_be_cached(request: HttpRequest) -> bool` - Indicates whether particular request could be saved / restored from cache.
- `cache_request_traits(request: HttpRequest) -> Tuple` - Gets tuple denoting request uniqueness. Requests with same results are treated as the same when caching.
- `override_config(config: Config)` - Overrides default parameters in config.

## Extensions example
**ext.py**
```python
from typing import Tuple

from nuclear.sublog import log

from xman.cache import sorted_dict_trait
from xman.config import Config
from xman.request import HttpRequest
from xman.response import HttpResponse
from xman.transform import replace_request_path


def transform_request(request: HttpRequest) -> HttpRequest:
    """Transforms each incoming Request before further processing (caching, forwarding)."""
    return replace_request_path(request, r'^/path/(.+?)(/[a-z]+)(/.*)', r'\3')


def transform_response(request: HttpRequest, response: HttpResponse) -> HttpResponse:
    """Transforms each Response before sending it."""
    if request.path.startswith('/api'):
        log.debug('Found Ya', path=request.path)
        response = response.set_content('{"payload": "anythingyouwish"}"')
    return response


def can_be_cached(request: HttpRequest) -> bool:
    """Indicates whether particular request could be saved / restored from cache."""
    return request.method in {'get', 'post'}


def cache_request_traits(request: HttpRequest) -> Tuple:
    """Gets tuple denoting request uniqueness. Requests with same results are treated as the same when caching."""
    return request.method, request.path, request.content, sorted_dict_trait(request.headers)


def override_config(config: Config):
    """Overrides default parameters in config."""
    config.verbose = True

```

# Run in docker
Create and customize `ext.py` and run:
```bash
docker run --rm -it --network=host -v `pwd`/ext.py:/ext.py \
  --name=xman igrek5151/xman:latest \
  --ext=/ext.py
```
Or run in background:
```bash
docker run -d --network=host -v `pwd`/ext.py:/ext.py \
  --name=xman igrek5151/xman:latest \
  --ext=/ext.py
```
