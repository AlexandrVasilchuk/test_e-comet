import logging

import asyncpg
import os

from aiohttp import ClientSession
from asyncpg import Connection
from http import HTTPStatus


async def create_connection() -> Connection:
    """
    Асинхронная функция для создания соединения с базой данных.

    Переменные для подключения должны быть указаны в переменных окружения.

    Returns:
        Connection: Объект соединения с базой данных.
    """

    user, password, database, host, port = (
        os.getenv("DB_USER"),
        os.getenv("DB_PASSWORD"),
        os.getenv("DB_NAME"),
        os.getenv("DB_HOST"),
        os.getenv("DB_PORT"),
    )
    return await asyncpg.connect(
        user=user, password=password, database=database, host=host, port=port
    )


async def request_detail(
    owner: str, repo_name: str, session: ClientSession
) -> dict:
    """
    Функция запроса к API GitHub для получения информации о репозитории.

    Args:
        owner: str - Владелец репозитория.
        repo_name: str - Название репозитория.
        session: ClientSession - Сессия для выполнения HTTP-запросов.

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
    db_connection: Connection,
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
        db_connection (Connection): Соединение с базой данных.
        full_name (str): Название репозитория.
        owner (str): Владелец репозитория.
        stars (int): Количество звезд у репозитория.
        watchers (int): Количество наблюдателей за репозиторием.
        forks (int): Количество форков репозитория.
        open_issues (int): Количество открытых проблем у репозитория.
        language (str): Язык программирования репозитория.
    """

    async with db_connection.transaction():
        await db_connection.execute(
            """
            INSERT INTO repositories (repo, owner, stars, watchers, forks, open_issues, language)
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


async def update_positions(db_connection: Connection):
    """
    Функция для обновления позиций репозиториев в БД на основе stars.

    Args:
        db_connection (Connection): Соединение с БД.
    """

    sorted_repositories = await db_connection.fetch(
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
            await db_connection.execute(
                """
                UPDATE repositories
                SET position_cur = $1, position_prev = $2
                WHERE id = $3
                """,
                position_curr,
                position_prev,
                repo_id,
            )
        else:
            await db_connection.execute(
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


async def parse_repositories_info(
    repositories: list[dict], db_connection: Connection, session: ClientSession
):
    """
    Парсинг информации о репозиториях и сохранение в БД.

    Args:
        repositories: list[dict] - Информация о репозиториях.
        db_connection: Connection - Соединение с БД.
        session: ClientSession - Сессия для отправки HTTP-запросов.
    """

    for repository in repositories:
        try:
            owner = repository.get("owner", {}).get("login")
            result = await request_detail(
                owner, repository.get("name"), session
            )

            if result.get("full_name") and result.get("stars"):
                await add_repository_to_database(
                    db_connection=db_connection, owner=owner, **result
                )
            else:
                logging.warning(
                    "Репозиторий пропущен, так как отсутсвуют поля repo или stars"
                )
        except Exception as e:
            logging.warning("Репозиторий пропущен. Возникла ошибка")


async def main(event, context):
    url = "https://api.github.com/repositories"
    headers = {"Accept": "application/vnd.github.v3+json"}
    counter = 0
    try:
        db_connection = await create_connection()
    except asyncpg.PostgresConnectionError:
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": "Ошибка подключения к базу",
        }
    try:
        async with ClientSession() as session:
            while url is not None and counter < 5:
                async with session.get(
                    str(url), headers=headers, ssl=False
                ) as response:
                    counter += 1
                    link_info = response.headers.get("link")

                    await parse_repositories_info(
                        await response.json(), db_connection, session
                    )

                    if link_info:
                        url = link_info.split(";", maxsplit=1)[0].strip("<>")
                    else:
                        url = None
    except Exception as e:
        logging.error("При работе парсера произошла ошибка. {}".format(e))

    await update_positions(db_connection)
    await db_connection.close()
    return {
        "statusCode": HTTPStatus.OK,
        "body": "Данный успешно сохранены в базу!",
    }
