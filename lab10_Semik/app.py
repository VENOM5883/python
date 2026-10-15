"""Лабораторная работа №10. HTTP и REST API (Flask).
Вариант 15. Медицинская клиника, ресурс Appointment, операция «свободные записи».
"""
from flask import Flask, jsonify

from exceptions import ApiError
from repository import AppointmentRepository
from routes import api
from service import AppointmentService

SEED = [
    {"doctor": "Смирнова Е.В.", "specialty": "терапевт", "date": "2026-10-20", "time": "09:00",
     "cabinet": 101, "patient": "Иванов И.И."},
    {"doctor": "Смирнова Е.В.", "specialty": "терапевт", "date": "2026-10-20", "time": "09:30",
     "cabinet": 101},
    {"doctor": "Смирнова Е.В.", "specialty": "терапевт", "date": "2026-10-20", "time": "10:00",
     "cabinet": 101},
    {"doctor": "Кузнецов О.П.", "specialty": "кардиолог", "date": "2026-10-20", "time": "09:00",
     "cabinet": 205, "patient": "Петрова А.С.", "status": "completed"},
    {"doctor": "Кузнецов О.П.", "specialty": "кардиолог", "date": "2026-10-21", "time": "11:00",
     "cabinet": 205},
    {"doctor": "Орлова Н.А.", "specialty": "невролог", "date": "2026-10-21", "time": "12:00",
     "cabinet": 310},
]


def error_response(code: str, message: str, status: int):
    return jsonify({"error": message, "code": code}), status


def create_app(seed: bool = True) -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    service = AppointmentService(AppointmentRepository())
    if seed:
        for data in SEED:
            service.create_appointment(data)
    app.config["SERVICE"] = service
    app.register_blueprint(api)

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return error_response(error.code, error.message, error.status_code)

    @app.errorhandler(404)
    def not_found(_):
        return error_response("NOT_FOUND", "Ресурс не найден или некорректный идентификатор", 404)

    @app.errorhandler(405)
    def method_not_allowed(_):
        return error_response("METHOD_NOT_ALLOWED", "Метод не поддерживается", 405)

    @app.errorhandler(500)
    def internal(_):
        return error_response("INTERNAL_ERROR", "Внутренняя ошибка сервера", 500)

    return app


if __name__ == "__main__":
    create_app().run(port=5000, debug=False)
