from typing import Optional

import asyncpg


_db_pool: Optional[asyncpg.Pool] = None
_raw_asyncpg_connect = asyncpg.connect


class PooledConnectionProxy:
    def __init__(self, pool: asyncpg.Pool, conn: asyncpg.Connection):
        self._pool = pool
        self._conn = conn
        self._released = False

    def __getattr__(self, item):
        return getattr(self._conn, item)

    async def close(self):
        if not self._released:
            self._released = True
            await self._pool.release(self._conn)


async def init_pool(database_url: str, min_size: int = 2, max_size: int = 20):
    global _db_pool
    _db_pool = await asyncpg.create_pool(
        database_url,
        min_size=min_size,
        max_size=max_size,
        command_timeout=120,
    )
    return _db_pool


async def close_pool():
    global _db_pool
    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None


def get_pool() -> Optional[asyncpg.Pool]:
    return _db_pool


def get_raw_connect():
    return _raw_asyncpg_connect


async def pooled_connect(*args, **kwargs):
    if _db_pool is None:
        return await _raw_asyncpg_connect(*args, **kwargs)

    if not args and not kwargs:
        conn = await _db_pool.acquire()
        return PooledConnectionProxy(_db_pool, conn)

    if len(args) == 1 and not kwargs:
        conn = await _db_pool.acquire()
        return PooledConnectionProxy(_db_pool, conn)

    return await _raw_asyncpg_connect(*args, **kwargs)


async def db_connect(database_url: str):
    if _db_pool is not None:
        conn = await _db_pool.acquire()
        return PooledConnectionProxy(_db_pool, conn)
    return await _raw_asyncpg_connect(database_url)


async def db_release(conn):
    if conn is None:
        return
    await conn.close()
