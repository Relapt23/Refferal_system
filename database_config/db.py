from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from database_config.config import db_config
from database_config.models import Base

engine = create_async_engine(
    f"postgresql+asyncpg://{db_config.USER}:{db_config.PASSWORD}@{db_config.HOST}:{db_config.PORT}/{db_config.DATABASE}",
    echo=True)
sess = async_sessionmaker(engine)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with sess() as session:
        yield session
