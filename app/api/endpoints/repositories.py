from http import HTTPStatus
from typing import Optional

from asyncpg.connection import Connection
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.db import get_db_async_connection
from app.schemas.activity import RepositoryActivity
from app.schemas.repository import RepositoryDB
from app.services import (
    GITHUB_ERROR,
    get_repositories_by_field,
    get_repository_activity,
)

router = APIRouter()


@router.get("/repos/top100", response_model=list[RepositoryDB])
async def get_top_repositories(
    sort_by: str = Query(
        "stars",
        description="Field to sort by",
        regex=r"^(stars|watchers|forks|open_issues)$",
    ),
    order: str = Query(
        "desc", description="Sort order", regex=r"^(asc|desc)$"
    ),
    connection: Connection = Depends(get_db_async_connection),
):
    return await get_repositories_by_field(sort_by, order, connection)


@router.get(
    "/repos/{owner}/{repo}/activity", response_model=list[RepositoryActivity]
)
async def get_activity(
    owner: str,
    repo: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
):
    try:
        return await get_repository_activity(owner, repo, since, until)
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=GITHUB_ERROR.format(e),
        )
