"""Локальная имитация CDN (разрешена методичкой, если внешний CDN недоступен).

origin  (порт 8001) — исходный сервер статики, без кэширования, с искусственной задержкой;
edge    (порт 8002) — «CDN-узел»: при первом запросе забирает файл с origin (MISS),
          затем отдаёт из своей памяти (HIT), добавляя Cache-Control, Age, ETag, X-Cache.
"""
import hashlib
import mimetypes
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STATIC = Path(__file__).with_name("static")
ORIGIN_PORT, EDGE_PORT = 8001, 8002
ORIGIN_DELAY = 0.15  # имитация удалённости origin-сервера
MAX_AGE = 3600


class OriginHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = (STATIC / self.path.removeprefix("/static/").lstrip("/")).resolve()
        if not path.is_file() or STATIC.resolve() not in path.parents:
            self.send_error(404)
            return
        time.sleep(ORIGIN_DELAY)
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *args):
        pass


class EdgeHandler(BaseHTTPRequestHandler):
    cache: dict[str, tuple[bytes, str, float]] = {}

    def do_GET(self):
        entry = self.cache.get(self.path)
        status = "HIT"
        if entry is None or time.time() - entry[2] > MAX_AGE:
            status = "MISS"
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{ORIGIN_PORT}{self.path}") as resp:
                    entry = (resp.read(), resp.headers["Content-Type"], time.time())
            except Exception:
                self.send_error(404)
                return
            self.cache[self.path] = entry
        content, content_type, stored = entry
        etag = '"' + hashlib.md5(content).hexdigest() + '"'
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", f"public, max-age={MAX_AGE}")
        self.send_header("Age", str(int(time.time() - stored)))
        self.send_header("ETag", etag)
        self.send_header("X-Cache", status)
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *args):
        pass


def start(background: bool = False):
    servers = [ThreadingHTTPServer(("127.0.0.1", ORIGIN_PORT), OriginHandler),
               ThreadingHTTPServer(("127.0.0.1", EDGE_PORT), EdgeHandler)]
    for server in servers:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"origin: http://127.0.0.1:{ORIGIN_PORT}/static/...  edge (CDN): http://127.0.0.1:{EDGE_PORT}/static/...")
    if not background:
        threading.Event().wait()
    return servers


if __name__ == "__main__":
    start()
