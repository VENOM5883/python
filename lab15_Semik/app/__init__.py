"""Application Factory."""
import logging

from flask import Flask, render_template, request

from app.config import Config
from app.database import Base, init_engine, make_session
from app.seed import seed


def create_app(config: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)
    app.json.ensure_ascii = False
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    engine = init_engine(config.DATABASE_URL)
    Base.metadata.create_all(engine)
    app.session = make_session(engine)
    seed(app.session)

    from app.routes.api import api
    from app.routes.web import web
    app.register_blueprint(web)
    app.register_blueprint(api)

    @app.teardown_appcontext
    def remove_session(_exc=None):
        app.session.remove()

    @app.after_request
    def log_request(response):
        app.logger.info("%s %s -> %s", request.method, request.path, response.status_code)
        return response

    @app.errorhandler(404)
    def not_found(_):
        if request.path.startswith("/api/"):
            return {"error": "Не найдено"}, 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_):
        return render_template("404.html", message="Внутренняя ошибка сервера"), 500

    app.logger.info("Приложение запущено, БД: %s", engine.url.render_as_string(hide_password=True))
    return app
