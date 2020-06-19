"""
Redis连接池管理
"""
import aioredis

from libs.tomlread import ConfEntity
from libs.decorators import singleton


__all__ = [
    'redis_pools'
]


@singleton
class Redis:
    redis_pools = {}

    def __init__(self):
        pass

    async def create_pools(self):
        _redis_pools = {}
        redis_conf = ConfEntity().redis
        for alias, cnf in redis_conf.items():
            address = cnf.pop('host')
            port = cnf.pop('port')
            conn = await aioredis.create_redis_pool((address, port), **cnf)
            _redis_pools[alias] = conn
        self.redis_pools = _redis_pools

    @property
    async def pools(self):
        if not self.redis_pools:
            await self.create_pools()
        return self.redis_pools


async def redis_pools(alias):
    pools = await Redis().pools
    return pools[alias]


"""EXAMPLE
import asyncio
from redis import redis_pools

async def main():
    redis = await redis_pools('default')

    await redis.hmset_dict('hash1',
                           key1='value1',
                           key2='value2',
                           key3=123)

    result = await redis.hgetall('hash', encoding='utf-8')

    redis.close()
    await redis.wait_closed()

asyncio.run(main())

"""