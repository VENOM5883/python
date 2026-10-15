"""Лабораторная работа №15. Flask. Вариант 15 — Аптека.  Запуск: python run.py"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["FLASK_ENV"] == "development")
