import logging
import os
import random
from collections import namedtuple
from http import HTTPStatus

import requests
import psycopg2
from psycopg2 import pool
from psycopg2.extensions import connection

MIN_CONNECTIONS_COUNT = 1
MAX_CONNECTIONS_COUNT = 10
Repository = namedtuple(
    "Repository",
    [
        "id",
        "repo",
        "owner",
        "position_cur",
        "position_prev",
        "stars",
        "watchers",
        "forks",
        "open_issues",
        "language",
    ],
)


def create_pool() -> pool.SimpleConnectionPool:
    """
    Создает пул соединений с базой данных.

    Переменные для подключения должны быть указаны в переменных окружения.

    Returns:
        pool.SimpleConnectionPool: Объект пула соединений с базой данных.
    """

    user, password, database, host, port = (
        os.getenv("DB_USER"),
        os.getenv("DB_PASSWORD"),
        os.getenv("DB_NAME"),
        os.getenv("DB_HOST"),
        os.getenv("DB_PORT"),
    )
    return pool.SimpleConnectionPool(
        MIN_CONNECTIONS_COUNT,
        MAX_CONNECTIONS_COUNT,
        user=user,
        password=password,
        database=database,
        host=host,
        port=port,
    )


def request_detail(owner: str, repo_name: str) -> dict:
    """
    Функция запроса к API GitHub для получения информации о репозитории.

    Args:
        owner: str - Владелец репозитория.
        repo_name: str - Название репозитория.

    Returns:
        dict: Информация о репозитории.
    """

    repo_info_url = "https://api.github.com/repos/{owner}/{repo_name}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(
        repo_info_url.format(owner=owner, repo_name=repo_name),
        headers=headers,
    )
    return parse_detail(response.json())


def parse_detail(repository: dict) -> dict:
    result = {
        "full_name": repository.get("full_name"),
        "stars": repository.get("stargazers_count"),
        "watchers": repository.get("watchers_count"),
        "forks": repository.get("forks_count"),
        "open_issues": repository.get("open_issues_count"),
        "language": repository.get("language"),
    }
    return result


def add_repository_to_database(
    db_connection: connection,
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
        db_connection: connection - Соединение с базой данных.
        full_name: str - Название репозитория.
        owner: str - Владелец репозитория.
        stars: int - Количество звезд у репозитория.
        watchers: int - Количество наблюдателей за репозиторием.
        forks: int - Количество форков репозитория.
        open_issues: int - Количество открытых проблем у репозитория.
        language: str - Язык программирования репозитория.
    """

    with db_connection:
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO repositories (
                repo, owner, stars, watchers, forks, open_issues, language
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (repo) DO UPDATE
                SET
                    owner = EXCLUDED.owner,
                    stars = EXCLUDED.stars,
                    watchers = EXCLUDED.watchers,
                    forks = EXCLUDED.forks,
                    open_issues = EXCLUDED.open_issues,
                    language = EXCLUDED.language
                """,
                (
                    full_name,
                    owner,
                    stars,
                    watchers,
                    forks,
                    open_issues,
                    language,
                ),
            )


def update_positions(db_connection: connection):
    """
    Функция для обновления позиций репозиториев в БД на основе stars.

    Args:
        db_connection - Соединение с БД.
    """
    with db_connection:
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM repositories ORDER BY stars DESC LIMIT 100
                """
            )
            position_curr = 1
            for repository in (
                Repository(*repo) for repo in cursor.fetchall()
            ):
                repo_id = repository.id
                position_prev = repository.position_cur
                if position_prev is None:
                    position_prev = position_curr
                cursor.execute(
                    """
                    UPDATE repositories
                    SET position_cur = %s, position_prev = %s
                    WHERE id = %s
                    """,
                    (position_curr, position_prev, repo_id),
                )
                position_curr += 1


def parse_repositories_info(
    repositories: list[dict], db_connection: connection
):
    """
    Парсинг информации о репозиториях и сохранение в БД.

    Args:
        repositories: list[dict] - Информация о репозиториях.
        db_connection: connection - Соединение с БД.
    """

    for repository in repositories:
        try:
            owner = repository.get("owner", {}).get("login")
            result = request_detail(owner, repository.get("name"))

            if result.get("full_name") and result.get("stars"):
                add_repository_to_database(
                    db_connection=db_connection, owner=owner, **result
                )
            else:
                logging.warning(
                    "Репозиторий пропущен, так как отсутсвуют repo или stars."
                )
        except Exception as e:
            logging.warning(
                "Репозиторий пропущен. Возникла ошибка {}".format(e)
            )


def main(event, context):
    url = (
        f"https://api.github.com/repositories?since={random.randint(1, 10**6)}"
    )
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('TOKEN')}",
    }

    try:
        pool = create_pool()
        db_connection = pool.getconn()
    except psycopg2.Error:
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": "Ошибка подключения к базе",
        }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        parse_repositories_info(response.json(), db_connection)
    except Exception as e:
        logging.exception(e)

    update_positions(db_connection)
    pool.closeall()
    return {
        "statusCode": HTTPStatus.OK,
        "body": "Данные успешно сохранены в базу!",
    }
