"""RedisCache: кэш приёмов (String + TTL), информация о врачах (Hash),
ближайшие приёмы (Sorted Set), расписание врача (List), последние запросы (List)."""
import json

APPOINTMENT_TTL = 120
DOCTOR_TTL = 600
SCHEDULE_TTL = 300


class RedisCache:
    def __init__(self, client) -> None:
        self.redis = client

    # String: кэш документа приёма (cache-aside)
    def get_appointment(self, appointment_id: str) -> dict | None:
        value = self.redis.get(f"appointment:{appointment_id}")
        return json.loads(value) if value else None

    def set_appointment(self, appointment: dict) -> None:
        self.redis.set(f"appointment:{appointment['_id']}", json.dumps(appointment, ensure_ascii=False),
                       ex=APPOINTMENT_TTL)

    def invalidate_appointment(self, appointment_id: str) -> None:
        self.redis.delete(f"appointment:{appointment_id}")

    def ttl(self, key: str) -> int:
        return self.redis.ttl(key)

    # Hash: кэш информации о враче
    def set_doctor(self, doctor: dict) -> None:
        key = f"doctor:{doctor['id']}"
        self.redis.hset(key, mapping={k: str(v) for k, v in doctor.items()})
        self.redis.expire(key, DOCTOR_TTL)

    def get_doctor(self, doctor_id: int) -> dict | None:
        return self.redis.hgetall(f"doctor:{doctor_id}") or None

    # List: расписание врача на дату
    def set_schedule(self, doctor_id: int, date: str, slots: list[str]) -> None:
        key = f"schedule:{doctor_id}:{date}"
        self.redis.delete(key)
        self.redis.rpush(key, "", *slots)  # пустой маркер позволяет кэшировать и пустое расписание
        self.redis.expire(key, SCHEDULE_TTL)

    def get_schedule(self, doctor_id: int, date: str) -> list[str] | None:
        key = f"schedule:{doctor_id}:{date}"
        if not self.redis.exists(key):
            return None
        return [slot for slot in self.redis.lrange(key, 0, -1) if slot]

    def invalidate_schedule(self, doctor_id: int, date: str) -> None:
        self.redis.delete(f"schedule:{doctor_id}:{date}")

    # Sorted Set: ближайшие приёмы (score = YYYYMMDDHHMM)
    def add_upcoming(self, appointment: dict) -> None:
        score = int(appointment["date"].replace("-", "") + appointment["time"].replace(":", ""))
        self.redis.zadd("upcoming", {appointment["_id"]: score})

    def remove_upcoming(self, appointment_id: str) -> None:
        self.redis.zrem("upcoming", appointment_id)

    def nearest(self, count: int = 5) -> list[tuple[str, float]]:
        return self.redis.zrange("upcoming", 0, count - 1, withscores=True)

    # List: последние поисковые запросы
    def log_query(self, text: str) -> None:
        self.redis.lpush("recent_queries", text)
        self.redis.ltrim("recent_queries", 0, 9)

    def recent_queries(self) -> list[str]:
        return self.redis.lrange("recent_queries", 0, -1)

    def keys(self) -> list[str]:
        return sorted(self.redis.keys("*"))

    def clear(self) -> None:
        self.redis.flushdb()
