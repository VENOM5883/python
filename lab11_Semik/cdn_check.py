"""Исследование CDN: заголовки, время, размер, первый и повторный запросы."""
import time

import requests

import cdn_server

RESOURCES = ["/static/images/doctor1.svg", "/static/images/doctor2.svg", "/static/css/style.css",
             "/static/js/app.js"]


def measure(url: str, headers: dict | None = None) -> tuple:
    start = time.perf_counter()
    response = requests.get(url, headers=headers or {}, timeout=5)
    return response, (time.perf_counter() - start) * 1000


def main() -> None:
    cdn_server.start(background=True)
    time.sleep(0.3)
    print(f"{'Ресурс':<30}{'Источник':<12}{'Код':>5}{'мс':>8}{'байт':>7}  Cache-Control / X-Cache / Age")
    for path in RESOURCES:
        origin = f"http://127.0.0.1:{cdn_server.ORIGIN_PORT}{path}"
        edge = f"http://127.0.0.1:{cdn_server.EDGE_PORT}{path}"
        for title, url in (("origin", origin), ("CDN #1", edge), ("CDN #2", edge)):
            response, ms = measure(url)
            h = response.headers
            print(f"{path:<30}{title:<12}{response.status_code:>5}{ms:>8.1f}{len(response.content):>7}  "
                  f"{h.get('Cache-Control')} / {h.get('X-Cache', '-')} / {h.get('Age', '-')}")
        etag = response.headers["ETag"]
        response, ms = measure(edge, {"If-None-Match": etag})
        print(f"{path:<30}{'CDN+ETag':<12}{response.status_code:>5}{ms:>8.1f}{len(response.content):>7}  304 Not Modified")


if __name__ == "__main__":
    main()
