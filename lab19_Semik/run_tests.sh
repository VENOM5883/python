#!/usr/bin/env bash
# Тесты каждого сервиса запускаются отдельно (у каждого свой пакет app)
set -e
cd "$(dirname "$0")"
python -m pytest -q -p no:cacheprovider tests
for service in product-service warehouse-service order-service notification-service gateway; do
  echo "== $service"
  (cd "$service" && python -m pytest -q -p no:cacheprovider tests)
done
