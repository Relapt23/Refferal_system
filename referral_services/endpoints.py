from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database_config.db import get_session
from database_config.models import Users, InvitedUsers
from database_config.schemas import SignUp, CustomException, Login
from referral_services.security import pwd_context, make_jwt_token, get_current_user
from referral_services.services import generate_referral_code, get_hunter_info
from referral_services.redis import get_redis
import redis.asyncio as redis

router = APIRouter()


@router.post("/sign_up")
async def sign_up(user: SignUp, session: AsyncSession = Depends(get_session)):
    query = await session.execute(select(Users).where(Users.email == user.email))
    get_user = query.scalar_one_or_none()

    if get_user:
        raise CustomException(detail="existing_user", status_code=400)

    hashed_password = pwd_context.hash(user.password)

    if user.referral_code:
        check_referral_code = await session.execute(select(Users).where(Users.referral_code == user.referral_code))
        referrer = check_referral_code.scalar_one_or_none()
        if referrer is None:
            raise CustomException(detail="invalid_referral_code", status_code=400)

    hunter_data = await get_hunter_info(user.email)
    new_user = Users(email=user.email, password=hashed_password, hunter_info=hunter_data)
    session.add(new_user)
    await session.commit()

    if user.referral_code:
        referral_entry = InvitedUsers(referral_code=user.referral_code, registered_user_email=user.email)
        session.add(referral_entry)

    await session.commit()
    return {"message": "Successfully!"}


@router.post("/login")
async def login(user: Login, session: AsyncSession = Depends(get_session)):
    query = await session.execute(select(Users).where(Users.email == user.email))
    result = query.scalar_one_or_none()

    if not result:
        raise CustomException(detail="user_not_found", status_code=404)
    if not pwd_context.verify(user.password, result.password):
        raise CustomException(detail="incorrect_name_or_password", status_code=400)

    token = make_jwt_token(user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/create_code")
async def create_referral_code(user: Users = Depends(get_current_user),
                               session: AsyncSession = Depends(get_session)):
    user.referral_code = generate_referral_code()
    await session.commit()
    await session.refresh(user)
    return {"message": f"Referral code for {user.email}", "referral_code": user.referral_code}


@router.get("/delete_code")
async def delete_referral_code(user: Users = Depends(get_current_user),
                               session: AsyncSession = Depends(get_session)):
    if not user.referral_code:
        raise CustomException(detail="referral_code_not_found", status_code=404)
    user.referral_code = None
    await session.commit()
    return {"message": "Successfully deleted"}


@router.get("/create_code/{email}")
async def get_referral_code(email: str, session: AsyncSession = Depends(get_session),
                            redis_client: redis.Redis = Depends(get_redis)):
    cached_code = await redis_client.get(email)
    if cached_code:
        return {"message": "Referral code from cache", "referral_code": cached_code}

    query = await session.execute(select(Users).where(Users.email == email))
    user = query.scalar_one_or_none()

    if not user:
        raise CustomException(detail="user_not_found", status_code=404)
    if user.referral_code is None:
        raise CustomException(detail="referral_code_not_found", status_code=404)

    await redis_client.set(email, user.referral_code, ex=3600)

    return {"message": "Referral code for this user", "referral_code": user.referral_code}


@router.get("/info/{id}")
async def get_info(id: int, session: AsyncSession = Depends(get_session)):
    query = await session.execute(select(Users).where(Users.id == id))
    user = query.scalar_one_or_none()

    if not user:
        raise CustomException(detail="user_not_found", status_code=404)

    invited_users_query = await session.execute(
        select(Users.email, Users.referral_code, Users.hunter_info)
        .join(InvitedUsers, Users.email == InvitedUsers.registered_user)
        .where(InvitedUsers.referral_code == user.referral_code)
    )
    invited_users = [
        {
            "email": email,
            "referral_code": referral_code,
            "hunter_data": hunter_info
        }
        for email, referral_code, hunter_info in invited_users_query.all()
    ]

    return {
        "email": user.email,
        "referral_code": user.referral_code,
        "invited_users": invited_users
    }
