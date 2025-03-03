from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database_config.db import get_session
from database_config.models import Users
from database_config.schemas import SignUp, CustomException
from security import pwd_context, make_jwt_token

router = APIRouter()


@router.post("/sign_up")
async def sign_up(user: SignUp, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Users).where(Users.username == user.username))
    res = result.scalar_one_or_none()
    if not res:
        hashed_password = pwd_context.hash(user.password)
        new_jwt = make_jwt_token(user.username)
        new_user = Users(username=user.username, password=hashed_password, jwt=new_jwt)
        session.add(new_user)
        await session.commit()
        response = JSONResponse({"message": "Успешная регистрация"})
        response.set_cookie("jwt", new_jwt)
        return response
    else:
        raise CustomException(detail="Пользователь с таким именем уже существует", status_code=404)
