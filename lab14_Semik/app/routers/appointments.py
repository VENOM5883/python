from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.cache import cache
from app.database import get_db
from app.repositories.appointment import AppointmentRepository
from app.schemas.appointment import (AppointmentCreate, AppointmentListResponse,
                                     AppointmentResponse, AppointmentUpdate, Statistics, Status)
from app.services.appointment import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Записи на приём"])

NOT_FOUND = {404: {"description": "Запись не найдена"}}


def get_service(db: Session = Depends(get_db)) -> AppointmentService:
    """Dependency Injection: сервис получает репозиторий и кэш."""
    return AppointmentService(AppointmentRepository(db), cache)


@router.get("", response_model=AppointmentListResponse, summary="Список записей",
            description="Фильтрация, сортировка (asc/desc) и пагинация (skip/limit)")
def list_appointments(
    specialty: str | None = None, doctor: str | None = None, status_: Status | None = Query(None, alias="status"),
    date_: date | None = Query(None, alias="date"),
    sort: str = "date", order: str = Query("asc", pattern="^(asc|desc)$"),
    skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100),
    service: AppointmentService = Depends(get_service),
):
    filters = {"specialty": specialty, "doctor": doctor,
               "status": status_.value if status_ else None, "date": date_}
    items, total = service.list(filters, sort, order, skip, limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/search", response_model=list[AppointmentResponse], summary="Поиск",
            description="Поиск по пациенту, врачу или специальности")
def search(q: str = Query(min_length=2), limit: int = Query(20, ge=1, le=100),
           service: AppointmentService = Depends(get_service)):
    return service.search(q, limit)


@router.get("/statistics", response_model=Statistics, summary="Статистика (async)")
async def statistics(service: AppointmentService = Depends(get_service)):
    return service.statistics()


@router.get("/{appointment_id}", response_model=AppointmentResponse, responses=NOT_FOUND,
            summary="Запись по id (кэшируется в Redis)")
def get_appointment(appointment_id: int, response: Response,
                    service: AppointmentService = Depends(get_service)):
    data = service.get(appointment_id)
    response.headers["X-Cache"] = "HIT" if service.last_source == "cache" else "MISS"
    return data


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED,
             responses={409: {"description": "Слот врача занят"}}, summary="Создать запись")
def create(payload: AppointmentCreate, service: AppointmentService = Depends(get_service)):
    return service.create(payload)


@router.put("/{appointment_id}", response_model=AppointmentResponse, responses=NOT_FOUND,
            summary="Полностью заменить запись")
def replace(appointment_id: int, payload: AppointmentCreate,
            service: AppointmentService = Depends(get_service)):
    return service.replace(appointment_id, payload)


@router.patch("/{appointment_id}", response_model=AppointmentResponse, responses=NOT_FOUND,
              summary="Частично изменить запись")
def patch(appointment_id: int, payload: AppointmentUpdate,
          service: AppointmentService = Depends(get_service)):
    return service.patch(appointment_id, payload)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND,
               summary="Удалить запись")
def delete(appointment_id: int, service: AppointmentService = Depends(get_service)):
    service.delete(appointment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
