"""HTTP-слой: маршруты не содержат бизнес-логики, только вызывают сервис."""
from flask import Blueprint, current_app, jsonify, request

from exceptions import ValidationError

api = Blueprint("api", __name__)


def service():
    return current_app.config["SERVICE"]


def json_body():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Ожидается JSON (Content-Type: application/json)")
    return data


@api.get("/appointments")
def list_appointments():
    filters = {key: request.args.get(key) for key in ("doctor", "specialty", "status", "date")}
    items = service().get_appointments(filters, request.args.get("sort"),
                                       request.args.get("order", "asc"))
    return jsonify([a.to_dict() for a in items])


@api.get("/appointments/free")
def free_appointments():
    items = service().free_appointments(request.args.get("specialty"), request.args.get("date"))
    return jsonify([a.to_dict() for a in items])


@api.get("/appointments/<int:appointment_id>")
def get_appointment(appointment_id):
    return jsonify(service().get_appointment(appointment_id).to_dict())


@api.post("/appointments")
def create_appointment():
    appointment = service().create_appointment(json_body())
    return jsonify(appointment.to_dict()), 201, {"Location": f"/appointments/{appointment.id}"}


@api.put("/appointments/<int:appointment_id>")
def replace_appointment(appointment_id):
    return jsonify(service().replace_appointment(appointment_id, json_body()).to_dict())


@api.patch("/appointments/<int:appointment_id>")
def patch_appointment(appointment_id):
    return jsonify(service().patch_appointment(appointment_id, json_body()).to_dict())


@api.delete("/appointments/<int:appointment_id>")
def delete_appointment(appointment_id):
    service().delete_appointment(appointment_id)
    return "", 204


@api.route("/appointments/<path:bad_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def invalid_identifier(bad_id):
    raise ValidationError(f"Некорректный идентификатор: {bad_id}")
