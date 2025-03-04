from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database_config.db import get_session
from database_config.models import Users
from database_config.schemas import SignUp, CustomException, Login
from security import pwd_context, make_jwt_token, oauth2_scheme, get_user_from_jwt_token
from typing_extensions import Annotated
from fastapi.responses import JSONResponse
import uuid
import base64


def generate_referral_code():
    uid = uuid.uuid4()
    code = base64.urlsafe_b64encode(uid.bytes).decode("utf-8")[:10]
    return code.upper()


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           session: AsyncSession = Depends(get_session)):
    username = get_user_from_jwt_token(token)
    result = await session.execute(select(Users).where(Users.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise CustomException(detail="Пользователь с таким именем не найден", status_code=404)
    return user


router = APIRouter()


@router.post("/sign_up")
async def sign_up(user: SignUp, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Users).where(Users.username == user.username))
    res = result.scalar_one_or_none()
    if not res:
        hashed_password = pwd_context.hash(user.password)
        new_user = Users(username=user.username, password=hashed_password)
        session.add(new_user)
        await session.commit()
        return JSONResponse({"message": "Успешная регистрация!"})
    else:
        raise CustomException(detail="Пользователь с таким именем уже существует", status_code=404)


@router.post("/login")
async def login(user: Login, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Users).where(Users.username == user.username))
    res = result.scalar_one_or_none()
    if not res:
        raise CustomException(detail="Пользователь с таким именем не найден", status_code=404)
    if not pwd_context.verify(user.password, res.password):
        raise CustomException(detail="Неверное имя или пароль", status_code=404)
    token = make_jwt_token(user.username)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/create_code")
async def create_referral_code(user: Users = Depends(get_current_user),
                               session: AsyncSession = Depends(get_session)):
    referral_code = generate_referral_code()
    user.referral_code = referral_code
    await session.commit()
    await session.refresh(user)
    return {"message": f"Реферальный код для {user.username} - {referral_code}"}
