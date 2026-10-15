"""Подключение к MongoDB (или mongomock при отсутствии сервера)."""
import os


def get_database(name: str = "clinic"):
    url = os.getenv("MONGO_URL")
    if url:
        from pymongo import MongoClient
        from pymongo.errors import PyMongoError
        client = MongoClient(url, serverSelectionTimeoutMS=2000)
        try:
            client.admin.command("ping")
            return client[name], "MongoDB"
        except PyMongoError as error:
            print(f"MongoDB недоступна ({error.__class__.__name__}), используется mongomock")
    import mongomock
    return mongomock.MongoClient()[name], "mongomock (имитация)"
