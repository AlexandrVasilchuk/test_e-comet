from typing import Optional

from fastapi import APIRouter, Depends

from app.api.services import get_repository_activity
from app.core.db import get_db_async_connection
from asyncpg.connection import Connection

from app.schemas.repository import RepositoryDB
from app.schemas.activity import RepositoryActivity

router = APIRouter()


@router.get("/repos/top100", response_model=list[RepositoryDB])
async def get_top_repositories(
    connection: Connection = Depends(get_db_async_connection),
):
    rows = await connection.fetch(
        "SELECT * FROM repositories ORDER BY stars DESC LIMIT 100"
    )
    return [
        RepositoryDB(
            **{key: value for key, value in row.items() if key != "id"}
        )
        for row in rows
    ]


@router.get(
    "/repos/{owner}/{repo}/activity", response_model=list[RepositoryActivity]
)
async def get_activity(
    owner: str,
    repo: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
):
    return await get_repository_activity(owner, repo, since, until)
