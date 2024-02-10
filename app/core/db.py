import asyncpg
from app.core.config import settings


async def create_connection():
    return await asyncpg.connect(
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        host="db",
    )


async def get_db_async_connection():
    connection = await create_connection()
    yield connection
