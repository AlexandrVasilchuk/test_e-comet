import asyncpg
from asyncpg import Pool

from app.core.config import config


async def create_connection_pool() -> Pool:
    return await asyncpg.create_pool(
        user=config.db_user,
        password=config.db_password,
        database=config.db_name,
        host="db",
    )


async def get_db_async_connection():
    pool = await create_connection_pool()
    async with pool.acquire() as connection:
        yield connection
