import datetime

from pydantic import BaseModel


class RepositoryActivity(BaseModel):
    date: datetime.date
    commits: int
    authors: list[str]
