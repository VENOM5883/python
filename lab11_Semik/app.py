"""Лабораторная работа №11. REST API + SQLite + Redis-кэш + CDN.
Вариант 15. Медицинская клиника (Appointment).
"""
from flask import Flask, jsonify

from cache import ScheduleCache, create_redis
from database import DB_PATH, connect, init_db
from exceptions import ApiError
from repository import AppointmentRepository
from routes import api
from service import AppointmentService


def create_app(db_path: str = DB_PATH, redis_client=None) -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    connection = connect(db_path)
    init_db(connection)
    cache = ScheduleCache(redis_client or create_redis())
    app.config["SERVICE"] = AppointmentService(AppointmentRepository(connection), cache)
    app.register_blueprint(api)

    @app.errorhandler(ApiError)
    def api_error(error):
        return jsonify({"error": error.message, "code": error.code}), error.status_code

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Ресурс не найден", "code": "NOT_FOUND"}), 404

    @app.errorhandler(405)
    def not_allowed(_):
        return jsonify({"error": "Метод не поддерживается", "code": "METHOD_NOT_ALLOWED"}), 405

    return app


if __name__ == "__main__":
    create_app().run(port=5000)
