"""Лабораторная работа №20. Контейнеризация и CI/CD. Вариант 15 — Аптека (приложение + БД)."""
import logging
import time
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from src import config
from src.database import Base, make_engine, make_session_factory, ping
from src.models import Medicine
from src.schemas import MedicineIn, MedicineOut, SaleIn, SaleOut
from src.services import ConflictError, NotFoundError, PharmacyService

SEED = [("Парацетамол", "обезболивающие", "45.00", 120), ("Ибупрофен", "обезболивающие", "89.00", 80),
        ("Лоратадин", "противоаллергические", "95.00", 60), ("Витамин D3", "витамины", "310.00", 35)]


def create_app(database_url: str | None = None) -> FastAPI:
    logging.basicConfig(level=config.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    log = logging.getLogger("pharmacy")
    engine = make_engine(database_url or config.database_url())
    Base.metadata.create_all(engine)
    SessionLocal = make_session_factory(engine)
    with SessionLocal() as session:
        if not session.query(Medicine).first():
            session.add_all(Medicine(name=n, category=c, price=Decimal(p), quantity=q) for n, c, p, q in SEED)
            session.commit()

    app = FastAPI(title="Pharmacy API", version=config.APP_VERSION)
    log.info("Application started, database: %s", engine.url.render_as_string(hide_password=True))

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        log.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code,
                 (time.perf_counter() - start) * 1000)
        return response

    @app.exception_handler(NotFoundError)
    async def not_found(_, error):
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(ConflictError)
    async def conflict(_, error):
        return JSONResponse(status_code=409, content={"detail": str(error)})

    def service():
        with SessionLocal() as session:
            yield PharmacyService(session)

    @app.get("/health")
    def health():
        database_ok = ping(engine)
        body = {"status": "healthy" if database_ok else "unhealthy", "database": database_ok,
                "version": config.APP_VERSION}
        return JSONResponse(status_code=200 if database_ok else 503, content=body)

    @app.get("/medicines", response_model=list[MedicineOut])
    def list_medicines(category: str | None = None, svc: PharmacyService = Depends(service)):
        return svc.list(category)

    @app.get("/medicines/{medicine_id}", response_model=MedicineOut)
    def get_medicine(medicine_id: int, svc: PharmacyService = Depends(service)):
        return svc.get(medicine_id)

    @app.post("/medicines", response_model=MedicineOut, status_code=201)
    def create_medicine(data: MedicineIn, svc: PharmacyService = Depends(service)):
        return svc.create(data.model_dump())

    @app.put("/medicines/{medicine_id}", response_model=MedicineOut)
    def update_medicine(medicine_id: int, data: MedicineIn, svc: PharmacyService = Depends(service)):
        return svc.update(medicine_id, data.model_dump())

    @app.delete("/medicines/{medicine_id}", status_code=204)
    def delete_medicine(medicine_id: int, svc: PharmacyService = Depends(service)):
        svc.delete(medicine_id)
        return Response(status_code=204)

    @app.post("/sales", response_model=SaleOut, status_code=201)
    def sell(data: SaleIn, svc: PharmacyService = Depends(service)):
        if data.quantity <= 0:
            raise HTTPException(400, "quantity must be positive")
        return svc.sell(data.medicine_id, data.quantity)

    return app


app = create_app()
