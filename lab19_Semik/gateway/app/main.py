"""API Gateway — единая точка входа: маршрутизация, Retry/Circuit Breaker, агрегированный health."""
from __future__ import annotations

import os

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from common import observability
from common.resilience import CircuitBreaker, ResilientClient, ServiceUnavailableError

ROUTES = {  # префикс URL -> (имя сервиса, переменная окружения, адрес по умолчанию)
    "products": ("product-service", "PRODUCT_URL", "http://127.0.0.1:8001"),
    "stock": ("warehouse-service", "WAREHOUSE_URL", "http://127.0.0.1:8002"),
    "reservations": ("warehouse-service", "WAREHOUSE_URL", "http://127.0.0.1:8002"),
    "orders": ("order-service", "ORDER_URL", "http://127.0.0.1:8003"),
    "notifications": ("notification-service", "NOTIFICATION_URL", "http://127.0.0.1:8004"),
}


def create_app(clients: dict[str, ResilientClient] | None = None) -> FastAPI:
    if clients is None:
        clients = {}
        for name, env, default in ROUTES.values():
            if name not in clients:
                clients[name] = ResilientClient(name, os.getenv(env, default), timeout=5,
                                                breaker=CircuitBreaker(name, 3, 15))
    app = FastAPI(title="Pharmacy API Gateway")
    observability.setup(app, "gateway")

    @app.exception_handler(ServiceUnavailableError)
    async def unavailable(_, error: ServiceUnavailableError):
        return JSONResponse(status_code=503, content={"detail": str(error)})

    @app.get("/health")
    def health():
        services = {}
        for name, client in clients.items():
            try:
                ok = client.request("GET", "/health").status_code == 200
            except ServiceUnavailableError:
                ok = False
            services[name] = {"status": "healthy" if ok else "unavailable", **client.breaker.status()}
        healthy = all(s["status"] == "healthy" for s in services.values())
        return JSONResponse(status_code=200 if healthy else 503,
                            content={"status": "healthy" if healthy else "degraded", "services": services})

    @app.api_route("/api/{resource}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    @app.api_route("/api/{resource}", methods=["GET", "POST", "PUT", "DELETE"])
    async def proxy(resource: str, request: Request, path: str = ""):
        if resource not in ROUTES:
            return JSONResponse(status_code=404, content={"detail": f"Unknown resource {resource}"})
        client = clients[ROUTES[resource][0]]
        url = f"/{resource}" + (f"/{path}" if path else "")
        body = await request.body()
        response = client.request(request.method, url, params=dict(request.query_params), content=body or None,
                                  headers={"Content-Type": request.headers.get("content-type", "application/json"),
                                           "X-Request-ID": request.headers.get("X-Request-ID", "")})
        return Response(content=response.content, status_code=response.status_code,
                        media_type=response.headers.get("content-type"))

    return app


app = create_app() if os.getenv("SERVICE_AUTOSTART", "1") == "1" else None
