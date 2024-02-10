from fastapi import APIRouter, Request, Depends
from app.core.db import get_db_async_connection
from asyncpg.connection import Connection

router = APIRouter()

@router.get("/repos/top100")
async def get_top_repositories(connection: Connection = Depends(get_db_async_connection)):
    return {"todo": await connection.fetch("SELECT * FROM repositories")}


@router.get("/repos/{owner}/{repo}/activity")
async def get_repository_activity():
    return {"todo": "dont know if i should get some info from sb or just parse response from githubapi"}

