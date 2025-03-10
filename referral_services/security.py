import os

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from database_config.db import get_session
from database_config.models import Users
from referral_services.schemas import CustomException

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
        raise CustomException(detail="error_getting_token", status_code=400)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           session: AsyncSession = Depends(get_session)) -> Users:
    email = get_user_from_jwt_token(token)

    query = await session.execute(
        select(Users)
        .where(Users.email == email)
    )
    user = query.scalar_one_or_none()

    if not user:
        raise CustomException(detail="user_not_found", status_code=404)

    return user
