import asyncio
import os
import random
from http import HTTPStatus

import asyncpg
from aiohttp import ClientSession
from asyncpg import Pool

MAX_CONNECTIONS = 150


async def create_connection() -> Pool:
    """
    Асинхронная функция для создания соединения с базой данных.

    Переменные для подключения должны быть указаны в переменных окружения.

    Returns:
        Pool: Объект пула соединений с базой данных.
    """

    user, password, database, host, port = (
        os.getenv("DB_USER"),
        os.getenv("DB_PASSWORD"),
        os.getenv("DB_NAME"),
        os.getenv("DB_HOST"),
        os.getenv("DB_PORT"),
    )
    return await asyncpg.create_pool(
        max_size=MAX_CONNECTIONS,
        user=user,
        password=password,
        database=database,
        host=host,
        port=port,
    )


async def request_detail(
    owner: str, repo_name: str, session: ClientSession
) -> dict:
    """
    Функция запроса к API GitHub для получения информации о репозитории.

    Args:
        owner (str): Владелец репозитория.
        repo_name (str): Название репозитория.
        session (ClientSession): Сессия для выполнения HTTP-запросов.

    Returns:
        dict: Информация о репозитории.
    """

    repo_info_url = "https://api.github.com/repos/{owner}/{repo_name}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    async with session.get(
        repo_info_url.format(owner=owner, repo_name=repo_name),
        headers=headers,
        ssl=False,
    ) as response:
        repository_info = await response.json()
        return await parse_detail(repository_info)


async def parse_detail(repository: dict) -> dict:
    result = {
        "full_name": repository.get("full_name"),
        "stars": repository.get("stargazers_count"),
        "watchers": repository.get("watchers_count"),
        "forks": repository.get("forks_count"),
        "open_issues": repository.get("open_issues_count"),
        "language": repository.get("language"),
    }
    return result


async def add_repository_to_database(
    pool: Pool,
    full_name: str,
    owner: str,
    stars: int,
    watchers: int,
    forks: int,
    open_issues: int,
    language: str,
):
    """
    Функция для добавления или обновления информации о репозитории в БД.

    Args:
        pool (Pool): Соединение с базой данных.
        full_name (str): Название репозитория.
        owner (str): Владелец репозитория.
        stars (int): Количество звезд у репозитория.
        watchers (int): Количество наблюдателей за репозиторием.
        forks (int): Количество форков репозитория.
        open_issues (int): Количество открытых проблем у репозитория.
        language (str): Язык программирования репозитория.
    """
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                """
                INSERT INTO repositories (
                repo, owner, stars, watchers, forks, open_issues, language
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (repo) DO UPDATE
                SET
                    owner = EXCLUDED.owner,
                    stars = EXCLUDED.stars,
                    watchers = EXCLUDED.watchers,
                    forks = EXCLUDED.forks,
                    open_issues = EXCLUDED.open_issues,
                    language = EXCLUDED.language
                """,
                full_name,
                owner,
                stars,
                watchers,
                forks,
                open_issues,
                language,
            )


async def update_positions(pool: Pool):
    """
    Функция для обновления позиций репозиториев в БД на основе stars.

    Args:
        pool (Pool): Соединение с БД.
    """
    async with pool.acquire() as connection:
        sorted_repositories = await connection.fetch(
            """
            SELECT * FROM repositories ORDER BY stars DESC LIMIT 100
            """
        )

        position_curr = 1
        for repository in sorted_repositories:
            repo_id = repository["id"]
            position_prev = repository["position_cur"]
            if position_prev is None:
                position_prev = position_curr
            await connection.execute(
                """
                UPDATE repositories
                SET position_cur = $1, position_prev = $2
                WHERE id = $3
                """,
                position_curr,
                position_prev,
                repo_id,
            )
            position_curr += 1


async def parse_repository_info(
    owner: str, repo: str, pool: Pool, session: ClientSession
):
    repository_info = await request_detail(owner, repo, session)
    if repository_info.get("full_name") and owner:
        await add_repository_to_database(
            pool=pool, owner=owner, **repository_info
        )


async def main(event, context):
    url = "https://api.github.com/repositories?since={repo_id}".format(
        repo_id=random.randint(1, 10**6)
    )
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('TOKEN')}",
    }
    try:
        pool = await create_connection()
    except asyncpg.PostgresConnectionError:
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": "Ошибка подключения к базе",
        }
    tasks = []
    try:
        async with ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                repositories = await response.json()
                for repository in repositories:
                    owner = repository.get("owner", {}).get("login")
                    repo = repository.get("name")
                    tasks.append(
                        parse_repository_info(owner, repo, pool, session)
                    )
                await asyncio.gather(*tasks)
    except Exception as e:
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": "При парсинге данных произошло ошибка. {}".format(e),
        }

    await update_positions(pool)
    await pool.close()
    pool.terminate()
    return {
        "statusCode": HTTPStatus.OK,
        "body": "Данные успешно сохранены в базу!",
    }
