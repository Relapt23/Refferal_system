from contextlib import asynccontextmanager

from fastapi import FastAPI

import endpoints
from database_config.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(endpoints.router)
