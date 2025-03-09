import redis.asyncio as redis
import os

REDIS_HOST = os.getenv("REDIS_HOST")

redis_client = redis.Redis(host=REDIS_HOST, decode_responses=True)


async def get_redis() -> redis.Redis:
    return redis_client
