"""Redis-кэш расписания врачей (cache-aside, TTL, инвалидирование).

Если сервер Redis недоступен (REDIS_URL не задан или не отвечает),
используется fakeredis — имитация Redis в памяти процесса.
"""
import json
import os

SCHEDULE_TTL = 60  # секунд


def create_redis():
    url = os.getenv("REDIS_URL")
    if url:
        import redis
        client = redis.Redis.from_url(url, decode_responses=True)
        try:
            client.ping()
            return client
        except redis.RedisError:
            pass
    import fakeredis
    return fakeredis.FakeRedis(decode_responses=True)


class ScheduleCache:
    def __init__(self, client) -> None:
        self.redis = client
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key(doctor_id: int, date: str) -> str:
        return f"schedule:{doctor_id}:{date}"

    def get(self, doctor_id: int, date: str):
        value = self.redis.get(self.key(doctor_id, date))          # GET
        self.redis.incr(f"stats:schedule_views:{doctor_id}")        # INCR
        if value is None:
            self.misses += 1
            return None
        self.hits += 1
        return json.loads(value)

    def set(self, doctor_id: int, date: str, data) -> None:
        key = self.key(doctor_id, date)
        self.redis.set(key, json.dumps(data, ensure_ascii=False))  # SET
        self.redis.expire(key, SCHEDULE_TTL)                         # EXPIRE

    def invalidate(self, doctor_id: int, date: str) -> None:
        self.redis.delete(self.key(doctor_id, date))                 # DELETE

    def ttl(self, doctor_id: int, date: str) -> int:
        return self.redis.ttl(self.key(doctor_id, date))

    def views(self, doctor_id: int) -> int:
        return int(self.redis.get(f"stats:schedule_views:{doctor_id}") or 0)
