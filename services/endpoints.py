from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database_config.db import get_session
from database_config.models import Users
from database_config.schemas import SignUp, CustomException, Login
from services.security import pwd_context, make_jwt_token, get_current_user
from services.referral_services import generate_referral_code

router = APIRouter()


@router.post("/sign_up")
async def sign_up(user: SignUp, session: AsyncSession = Depends(get_session)):
    query = await session.execute(select(Users).where(Users.email == user.email))
    result = query.scalar_one_or_none()
    if result:
        raise CustomException(detail="Пользователь с таким именем уже существует", status_code=404)
    hashed_password = pwd_context.hash(user.password)
    new_user = Users(email=user.email, password=hashed_password)
    session.add(new_user)
    await session.commit()
    return {"message": "Успешная регистрация!"}


@router.post("/login")
async def login(user: Login, session: AsyncSession = Depends(get_session)):
    query = await session.execute(select(Users).where(Users.email == user.email))
    result = query.scalar_one_or_none()
    if not result:
        raise CustomException(detail="Пользователь с таким именем не найден", status_code=404)
    if not pwd_context.verify(user.password, result.password):
        raise CustomException(detail="Неверное имя или пароль", status_code=404)
    token = make_jwt_token(user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/create_code")
async def create_referral_code(user: Users = Depends(get_current_user),
                               session: AsyncSession = Depends(get_session)):
    referral_code = generate_referral_code()
    user.referral_code = referral_code
    await session.commit()
    await session.refresh(user)
    return {"message": f"Реферальный код для {user.email} - {referral_code}"}


@router.get("/delete_code")
async def delete_referral_code(user: Users = Depends(get_current_user),
                               session: AsyncSession = Depends(get_session)):
    if not user.referral_code:
        raise CustomException(detail="У вас нет реферального кода", status_code=404)
    user.referral_code = None
    await session.commit()
    return {"message": "Реферальный код успешно удален"}


@router.get("/create_code/{email}")
async def get_referral_code(email: str, session: AsyncSession = Depends(get_session)):
    query = await session.execute(select(Users).where(Users.email == email))
    user = query.scalar_one_or_none()
    if not user:
        raise CustomException(detail="Пользователь не найден", status_code=404)
    if user.referral_code is None:
        raise CustomException(detail="Реферальный код не найден", status_code=404)
    return {"message": f"Реферальный код данного пользователя - {user.referral_code}"}
