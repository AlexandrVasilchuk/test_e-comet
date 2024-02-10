from pydantic import BaseModel


class RepositoryDB(BaseModel):
    repo: str
    owner: str
    position_curr: int = 0
    position_prev: int = 0
    stars: int
    watchers: int
    forks: int
    open_issues: int
    language: str
