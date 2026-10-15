"""Демонстрация работы системы через Gateway: заказ, резерв, событие, Retry и Circuit Breaker.
Запускает сервисы сам (как run_local.py), останавливает склад и показывает поведение системы.
"""
import json
import shutil
import time

import httpx

import run_local

GATEWAY = "http://127.0.0.1:8000"


def show(title: str, response: httpx.Response) -> None:
    print(f"\n=== {title}: HTTP {response.status_code}")
    try:
        print(json.dumps(response.json(), ensure_ascii=False, indent=2)[:900])
    except ValueError:
        print(response.text[:300])


def wait_ready(timeout: float = 20) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{GATEWAY}/health", timeout=2).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    raise SystemExit("Сервисы не запустились, см. .local/*.log")


def main() -> None:
    shutil.rmtree(run_local.DATA, ignore_errors=True)
    processes = {name: run_local.start_service(name, port) for name, port in run_local.SERVICES}
    try:
        wait_ready()
        client = httpx.Client(base_url=GATEWAY, timeout=30)
        show("Health через Gateway", client.get("/health"))
        show("Каталог (product-service)", client.get("/api/products"))
        show("Остатки до заказа (warehouse-service)", client.get("/api/stock/1"))
        order = client.post("/api/orders", json={"customer": "Семик А.", "items": [
            {"product_id": 1, "quantity": 3}, {"product_id": 4, "quantity": 1}]})
        show("Создание заказа: order -> product + warehouse (резерв)", order)
        show("Остатки после заказа: товар зарезервирован", client.get("/api/stock/1"))
        show("Нет нужного количества (409)", client.post("/api/orders", json={
            "customer": "Петров П.", "items": [{"product_id": 5, "quantity": 1}]}))
        show("Рецептурный препарат без рецепта (400)", client.post("/api/orders", json={
            "customer": "Петров П.", "items": [{"product_id": 3, "quantity": 1}]}))
        time.sleep(1.5)
        show("Асинхронное событие OrderCreated получено notification-service", client.get("/api/notifications"))

        print("\n>>> Останавливаем warehouse-service (имитация docker compose stop warehouse-service)")
        processes["warehouse-service"].terminate()
        processes["warehouse-service"].wait()
        for attempt in range(1, 5):
            start = time.perf_counter()
            response = client.post("/api/orders", json={"customer": "Иванов И.", "items": [{"product_id": 2, "quantity": 1}]})
            print(f"Заказ при недоступном складе #{attempt}: HTTP {response.status_code} за "
                  f"{(time.perf_counter() - start) * 1000:.0f} мс — {response.json()['detail']}")
        show("Состояние Circuit Breaker в order-service", httpx.get("http://127.0.0.1:8003/health"))

        print("\n>>> Запускаем warehouse-service снова и ждём reset_timeout (10 c)")
        processes["warehouse-service"] = run_local.start_service("warehouse-service", 8002)
        time.sleep(11)
        show("Запрос после восстановления (HALF_OPEN -> CLOSED)", client.post("/api/orders", json={
            "customer": "Иванов И.", "items": [{"product_id": 2, "quantity": 1}]}))
        show("Circuit Breaker закрыт", httpx.get("http://127.0.0.1:8003/health"))
    finally:
        for process in processes.values():
            process.terminate()


if __name__ == "__main__":
    main()
