from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from database_config.config import db_config
from database_config.models import Base

engine = create_async_engine(
    f"postgresql+asyncpg://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}",
    echo=True)
sess = async_sessionmaker(engine)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with sess() as session:
        yield session
