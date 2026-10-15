"""Журнал запросов сервиса: timestamp, service, request id, метод, endpoint, статус, время."""
import logging
import time
import uuid

from fastapi import FastAPI, Request


def setup(app: FastAPI, service_name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO,
                        format=f"%(asctime)s {service_name} %(levelname)s %(message)s")
    log = logging.getLogger(service_name)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:8])
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        log.info("request_id=%s %s %s status=%s duration=%.0fms", request_id, request.method,
                 request.url.path, response.status_code, (time.perf_counter() - start) * 1000)
        return response

    return log
