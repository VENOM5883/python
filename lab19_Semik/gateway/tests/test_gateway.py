import httpx
from fastapi.testclient import TestClient

from app.main import create_app
from common.resilience import CircuitBreaker, ResilientClient


def make_client(handler, name):
    return ResilientClient(name, f"http://{name}", attempts=1, breaker=CircuitBreaker(name, 1, 60),
                           transport=httpx.MockTransport(handler))


def ok_handler(request):
    if request.url.path == "/health":
        return httpx.Response(200, json={"status": "healthy"})
    return httpx.Response(200, json={"path": request.url.path, "query": str(request.url.query, "utf-8")})


def down_handler(request):
    raise httpx.ConnectError("refused", request=request)


def clients(down=None):
    names = ["product-service", "warehouse-service", "order-service", "notification-service"]
    return {n: make_client(down_handler if n == down else ok_handler, n) for n in names}


def test_routing_to_services():
    client = TestClient(create_app(clients()))
    assert client.get("/api/products/1").json()["path"] == "/products/1"
    assert client.get("/api/stock", params={"a": 1}).json() == {"path": "/stock", "query": "a=1"}
    assert client.get("/api/unknown").status_code == 404


def test_health_reports_unavailable_service():
    response = TestClient(create_app(clients(down="warehouse-service"))).get("/health")
    assert response.status_code == 503
    assert response.json()["services"]["warehouse-service"]["status"] == "unavailable"


def test_unavailable_service_returns_503():
    client = TestClient(create_app(clients(down="order-service")))
    assert client.get("/api/orders").status_code == 503
    assert "Circuit Breaker" in client.get("/api/orders").json()["detail"]
