import os
from pydantic import BaseModel


class DBConfig(BaseModel):
    host: str = os.getenv("DB_HOST")
    port: str = os.getenv("DB_PORT")
    user: str = os.getenv("POSTGRES_USER")
    password: str = os.getenv("POSTGRES_PASSWORD")
    database: str = os.getenv("POSTGRES_DB")


db_config = DBConfig()
