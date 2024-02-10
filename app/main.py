from fastapi import FastAPI
from app.api.endpoints import repository_router


app = FastAPI()
app.include_router(repository_router, prefix="/api")
