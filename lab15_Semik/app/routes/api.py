"""REST API (JSON)."""
from flask import Blueprint, current_app, jsonify, request

from app.services.services import PharmacyService, ServiceError

api = Blueprint("api", __name__, url_prefix="/api")


def service() -> PharmacyService:
    return PharmacyService(current_app.session)


@api.errorhandler(ServiceError)
def service_error(error):
    return jsonify({"error": str(error)}), error.status


@api.get("/medicines")
def list_medicines():
    medicines = service().list_medicines(search=request.args.get("search"),
                                         category_id=request.args.get("category", type=int),
                                         in_stock=request.args.get("in_stock") == "true",
                                         sort=request.args.get("sort", "name"))
    return jsonify([m.to_dict() for m in medicines])


@api.get("/medicines/<int:medicine_id>")
def get_medicine(medicine_id):
    return jsonify(service().get_medicine(medicine_id).to_dict())


@api.post("/medicines")
def create_medicine():
    medicine = service().create_medicine(request.get_json(silent=True) or {})
    return jsonify(medicine.to_dict()), 201


@api.route("/medicines/<int:medicine_id>", methods=["PUT", "PATCH"])
def update_medicine(medicine_id):
    data = request.get_json(silent=True) or {}
    return jsonify(service().update_medicine(medicine_id, data, partial=request.method == "PATCH").to_dict())


@api.delete("/medicines/<int:medicine_id>")
def delete_medicine(medicine_id):
    service().delete_medicine(medicine_id)
    return "", 204


@api.post("/purchases")
def create_purchase():
    data = request.get_json(silent=True) or {}
    items = {int(k): int(v) for k, v in (data.get("items") or {}).items()}
    purchase = service().create_purchase(data.get("customer_name", ""), items)
    return jsonify({"id": purchase.id, "total": float(purchase.total)}), 201
