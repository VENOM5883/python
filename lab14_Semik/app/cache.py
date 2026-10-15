"""Redis-кэш (cache-aside). Без REDIS_URL используется fakeredis."""
import json

from app.config import settings


def create_redis():
    if settings.redis_url:
        import redis
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True,
                                      socket_connect_timeout=2)
        try:
            client.ping()
            return client
        except redis.RedisError:
            pass
    import fakeredis
    return fakeredis.FakeRedis(decode_responses=True)


class AppointmentCache:
    def __init__(self, client, ttl: int = settings.cache_ttl) -> None:
        self.redis = client
        self.ttl = ttl

    @staticmethod
    def key(appointment_id: int) -> str:
        return f"appointment:{appointment_id}"

    def get(self, appointment_id: int) -> dict | None:
        try:
            value = self.redis.get(self.key(appointment_id))
        except Exception:
            return None  # недоступность Redis не должна ломать API
        return json.loads(value) if value else None

    def set(self, appointment_id: int, data: dict) -> None:
        try:
            self.redis.set(self.key(appointment_id), json.dumps(data, ensure_ascii=False), ex=self.ttl)
        except Exception:
            pass

    def invalidate(self, appointment_id: int) -> None:
        try:
            self.redis.delete(self.key(appointment_id))
        except Exception:
            pass


cache = AppointmentCache(create_redis())
