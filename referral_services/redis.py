from redis.asyncio import Redis
import os

REDIS_HOST = os.getenv("REDIS_HOST")

redis_client = Redis(host=REDIS_HOST, decode_responses=True)


async def get_redis() -> Redis:
    return redis_client
