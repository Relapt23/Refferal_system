import os
from pydantic import BaseModel


class DBConfig(BaseModel):
    HOST: str = os.getenv("DB_HOST")
    PORT: str = os.getenv("DB_PORT")
    USER: str = os.getenv("POSTGRES_USER")
    PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    DATABASE: str = os.getenv("POSTGRES_DB")


db_config = DBConfig()
