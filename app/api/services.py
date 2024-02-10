from collections import defaultdict
from datetime import datetime
from http import HTTPStatus
from typing import Optional

from aiohttp import ClientSession
from fastapi import HTTPException

from app.schemas.activity import RepositoryActivity


GITHUB_ERROR = "Ошибка со стороны GitHub API"


async def get_repository_activity(
    owner: str,
    repo: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> list[RepositoryActivity]:
    params = {"per_page": 100}
    if since:
        params["since"] = since
    if until:
        params["until"] = until

    activity = defaultdict(lambda: {"commits": 0, "authors": set()})
    async with ClientSession() as session:
        page = 1
        while True:
            params["page"] = page
            commits = await fetch_commits(owner, repo, session, params)
            if not commits:
                break
            for commit in commits:
                commit_info = commit["commit"]
                commit_date = commit_info["author"]["date"][:10]
                activity[commit_date]["commits"] += 1

                author_name = commit_info["author"]["name"]
                activity[commit_date]["authors"].add(author_name)
            page += 1

    activity_list = [
        RepositoryActivity(
            date=datetime.fromisoformat(date),
            commits=data["commits"],
            authors=list(data["authors"]),
        )
        for date, data in activity.items()
    ]
    return activity_list


async def fetch_commits(
    owner: str, repo: str, session: ClientSession, params: dict
) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    async with session.get(url, params=params, ssl=False) as response:
        if response.status != HTTPStatus.OK:
            raise HTTPException(
                status_code=response.status, detail=GITHUB_ERROR
            )
        return await response.json()
