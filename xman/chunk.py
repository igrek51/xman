from typing import Iterable, Sequence


def send_chunked_response(wfile, content: bytes):
    content_chunks: Iterable[bytes] = chunks(content, 512)
    for chunk in content_chunks:
        tosend = ('%X' % len(chunk)).encode('utf-8') + b'\r\n' + chunk + b'\r\n'
        wfile.write(tosend)
    wfile.write('0\r\n\r\n'.encode('utf-8'))


def chunks(lst: Sequence, n: int) -> Iterable:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
