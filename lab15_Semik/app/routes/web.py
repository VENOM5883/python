"""HTML-интерфейс (Jinja2)."""
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from app.services.services import NotFound, PharmacyService, ServiceError

web = Blueprint("web", __name__)


def service() -> PharmacyService:
    return PharmacyService(current_app.session)


@web.route("/")
def index():
    return render_template("index.html", stats=service().stats())


@web.route("/medicines")
def medicine_list():
    filters = {"search": request.args.get("search", "").strip() or None,
               "category_id": request.args.get("category", type=int),
               "in_stock": request.args.get("in_stock") == "on",
               "prescription": request.args.get("prescription") or None,
               "sort": request.args.get("sort", "name")}
    return render_template("list.html", medicines=service().list_medicines(**filters),
                           categories=service().list_categories(), args=request.args)


@web.route("/medicines/<int:medicine_id>")
def medicine_detail(medicine_id):
    try:
        medicine = service().get_medicine(medicine_id)
    except NotFound:
        abort(404)
    return render_template("detail.html", medicine=medicine)


@web.route("/medicines/create", methods=["GET", "POST"])
def medicine_create():
    if request.method == "POST":
        try:
            medicine = service().create_medicine(request.form.to_dict())
            current_app.logger.info("Создан препарат %s", medicine.name)
            flash("Препарат добавлен", "success")
            return redirect(url_for("web.medicine_detail", medicine_id=medicine.id))
        except ServiceError as error:
            flash(str(error), "error")
            return render_template("create.html", categories=service().list_categories(),
                                   form=request.form), error.status
    return render_template("create.html", categories=service().list_categories(), form={})


@web.route("/medicines/<int:medicine_id>/edit", methods=["GET", "POST"])
def medicine_edit(medicine_id):
    try:
        medicine = service().get_medicine(medicine_id)
    except NotFound:
        abort(404)
    if request.method == "POST":
        data = request.form.to_dict()
        data.setdefault("prescription_required", "off")
        try:
            service().update_medicine(medicine_id, data)
            current_app.logger.info("Изменён препарат %s", medicine_id)
            flash("Изменения сохранены", "success")
            return redirect(url_for("web.medicine_detail", medicine_id=medicine_id))
        except ServiceError as error:
            flash(str(error), "error")
    return render_template("edit.html", medicine=medicine, categories=service().list_categories())


@web.post("/medicines/<int:medicine_id>/delete")
def medicine_delete(medicine_id):
    try:
        service().delete_medicine(medicine_id)
        current_app.logger.warning("Удалён препарат %s", medicine_id)
        flash("Препарат удалён", "success")
        return redirect(url_for("web.medicine_list"))
    except NotFound:
        abort(404)
    except ServiceError as error:
        flash(str(error), "error")
        return redirect(url_for("web.medicine_detail", medicine_id=medicine_id))


@web.route("/categories/<int:category_id>")
def category_detail(category_id):
    try:
        category = service().get_category(category_id)
    except NotFound:
        abort(404)
    return render_template("category.html", category=category)


@web.route("/purchases", methods=["GET", "POST"])
def purchases():
    medicines = service().list_medicines(in_stock=True)
    if request.method == "POST":
        items = {}
        for medicine in medicines:
            value = request.form.get(f"qty_{medicine.id}", "0").strip() or "0"
            if value.isdigit() and int(value) > 0:
                items[medicine.id] = int(value)
        try:
            purchase = service().create_purchase(request.form.get("customer_name", ""), items)
            current_app.logger.info("Покупка #%s на %s руб.", purchase.id, purchase.total)
            flash(f"Покупка №{purchase.id} оформлена на сумму {purchase.total} руб.", "success")
            return redirect(url_for("web.purchases"))
        except ServiceError as error:
            flash(str(error), "error")
            medicines = service().list_medicines(in_stock=True)
    return render_template("purchases.html", medicines=medicines, purchases=service().list_purchases())
