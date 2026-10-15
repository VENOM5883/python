"""Локальный запуск всей системы без Docker (SQLite + файловый брокер) — имитация docker compose.
Каждый сервис — отдельный процесс uvicorn со своей БД.  Запуск: python run_local.py
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / ".local"
SERVICES = [("product-service", 8001), ("warehouse-service", 8002), ("order-service", 8003),
            ("notification-service", 8004), ("gateway", 8000)]


def start_service(name: str, port: int) -> subprocess.Popen:
    DATA.mkdir(exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(ROOT), "EVENTS_DIR": str(DATA / "events"),
           "DATABASE_URL": f"sqlite:///{DATA / (name + '.db')}",
           "PRODUCT_URL": "http://127.0.0.1:8001", "WAREHOUSE_URL": "http://127.0.0.1:8002",
           "ORDER_URL": "http://127.0.0.1:8003", "NOTIFICATION_URL": "http://127.0.0.1:8004"}
    log = open(DATA / f"{name}.log", "a", encoding="utf-8")
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
                            cwd=ROOT / name, env=env, stdout=log, stderr=subprocess.STDOUT)


def main() -> None:
    processes = {name: start_service(name, port) for name, port in SERVICES}
    print("Запущено:", ", ".join(f"{n}:{p}" for n, p in SERVICES), "\nЛоги:", DATA, "\nCtrl+C — остановка")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes.values():
            process.send_signal(signal.SIGINT)


if __name__ == "__main__":
    main()
