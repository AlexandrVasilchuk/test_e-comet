from typing import Optional

from pydantic import BaseModel


class RepositoryDB(BaseModel):
    repo: str
    owner: str
    position_cur: Optional[int] = 0
    position_prev: Optional[int] = 0
    stars: int
    watchers: int
    forks: int
    open_issues: int
    language: Optional[str] = "Undefined"
