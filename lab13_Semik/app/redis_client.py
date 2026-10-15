"""Подключение к Redis (или fakeredis при отсутствии сервера)."""
import os


def get_redis():
    url = os.getenv("REDIS_URL")
    if url:
        import redis
        client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        try:
            client.ping()
            return client, "Redis"
        except redis.RedisError as error:
            print(f"Redis недоступен ({error.__class__.__name__}), используется fakeredis")
    import fakeredis
    return fakeredis.FakeRedis(decode_responses=True), "fakeredis (имитация)"
