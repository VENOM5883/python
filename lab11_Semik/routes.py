from flask import Blueprint, current_app, jsonify, request

from exceptions import ValidationError

api = Blueprint("api", __name__)


def service():
    return current_app.config["SERVICE"]


def body():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Ожидается JSON")
    return data


@api.get("/appointments")
def list_appointments():
    filters = {k: request.args.get(k) for k in ("doctor_id", "specialty", "status", "date")}
    return jsonify(service().list_appointments(filters, request.args.get("sort"), request.args.get("order", "asc")))


@api.get("/appointments/free")
def free():
    return jsonify(service().free(request.args.get("specialty"), request.args.get("date")))


@api.get("/appointments/<int:appointment_id>")
def get_one(appointment_id):
    return jsonify(service().get(appointment_id))


@api.post("/appointments")
def create():
    return jsonify(service().create(body())), 201


@api.put("/appointments/<int:appointment_id>")
def put(appointment_id):
    return jsonify(service().update(appointment_id, body(), partial=False))


@api.patch("/appointments/<int:appointment_id>")
def patch(appointment_id):
    return jsonify(service().update(appointment_id, body(), partial=True))


@api.delete("/appointments/<int:appointment_id>")
def delete(appointment_id):
    service().delete(appointment_id)
    return "", 204


@api.post("/appointments/<int:appointment_id>/complete")
def complete(appointment_id):
    return jsonify(service().complete(appointment_id, body().get("services")))


@api.get("/doctors/<int:doctor_id>/schedule")
def schedule(doctor_id):
    date = request.args.get("date")
    if not date:
        raise ValidationError("Параметр date обязателен")
    return jsonify(service().schedule(doctor_id, date))
