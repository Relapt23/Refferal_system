import os
import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from database_config.models import Users
from database_config.schemas import CustomException
from database_config.db import get_session
from typing_extensions import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def make_jwt_token(username):
    return jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)


def get_user_from_jwt_token(jwt_token: str):
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        return CustomException(detail="Ошибка получения JWT", status_code=400)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           session: AsyncSession = Depends(get_session)):
    email = get_user_from_jwt_token(token)
    result = await session.execute(select(Users).where(Users.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise CustomException(detail="Пользователь с таким именем не найден", status_code=404)
    return user
