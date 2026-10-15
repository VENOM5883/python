"""Проверка состояния контейнера без curl (в slim-образе его нет)."""
import sys
import urllib.request

try:
    with urllib.request.urlopen("http://localhost:8000/health", timeout=3) as response:
        sys.exit(0 if response.status == 200 else 1)
except Exception:  # noqa: BLE001
    sys.exit(1)
