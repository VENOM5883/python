"""Итоговый проект (лабораторная №21). Вариант 15 — Аптека: каталог, покупатели, заказы, склады,
контроль остатков. FastAPI + SQLAlchemy + PostgreSQL, JWT, роли USER/ADMIN.
"""
import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.api.routes import auth, orders, products, warehouses
from app.config import settings
from app.database import Base, make_engine
from app.exceptions import register_handlers
from app.seed import seed


def create_app(database_url: str | None = None) -> FastAPI:
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    log = logging.getLogger("pharmacy")
    engine = make_engine(database_url or settings.database_url)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as session:
        seed(session)

    app = FastAPI(title="Pharmacy API", version="1.0.0",
                  description="Итоговый проект: аптека — каталог, склады, заказы, контроль остатков",
                  docs_url="/swagger", redoc_url="/redoc")
    app.state.session_factory = session_factory
    register_handlers(app, log)
    for router in (auth, products, warehouses, orders):
        app.include_router(router)

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        log.info("%s %s status=%s duration=%.0fms", request.method, request.url.path, response.status_code,
                 (time.perf_counter() - start) * 1000)
        return response

    @app.get("/health", tags=["Служебные"])
    def health():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {"status": "healthy"}
        except Exception:  # noqa: BLE001
            return JSONResponse(status_code=503, content={"status": "unhealthy"})

    log.info("Application started")
    return app


app = create_app()
