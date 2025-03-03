from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database_config.config import DB_CONFIG
from database_config.models import Base

engine = create_async_engine(
    f"postgresql+asyncpg://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}",
    echo=True)
sess = async_sessionmaker(engine)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with sess() as session:
        yield session
