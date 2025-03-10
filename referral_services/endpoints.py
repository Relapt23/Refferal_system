import json
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database_config.db import get_session
from database_config.models import Users, InvitedUsers, ReferralCodes
from referral_services.redis import get_redis
from referral_services.schemas import CustomException, CreateReferralCodeParams
from referral_services.schemas import SignUpParams, LoginParams
from referral_services.security import pwd_context, make_jwt_token, get_current_user
from referral_services.services import generate_referral_code, get_hunter_info

router = APIRouter()


@router.post("/sign_up")
async def sign_up(params: SignUpParams, session: AsyncSession = Depends(get_session)):
    query = await session.execute(
        select(Users)
        .where(Users.email == params.email)
    )
    get_user = query.scalar_one_or_none()

    if get_user:
        raise CustomException(detail="existing_user", status_code=400)

    hashed_password = pwd_context.hash(params.password)

    referrer_id: Optional[int] = None

    if params.referral_code:
        query = await session.execute(
            select(ReferralCodes)
            .where(ReferralCodes.referral_code == params.referral_code)
            .order_by(ReferralCodes.id.desc())
        )
        referral_code = query.scalar_one_or_none()

        if referral_code is None:
            raise CustomException(detail="invalid_referral_code", status_code=400)
        if referral_code.end_date.timestamp() < datetime.now().timestamp():
            raise CustomException(detail="expired_referral_code", status_code=400)

        referrer_id = referral_code.referrer_id

    hunter_data = await get_hunter_info(params.email)
    new_user = Users(email=params.email, password_hash=hashed_password, hunter_info=hunter_data)
    session.add(new_user)
    await session.commit()

    if referrer_id:
        referral_entry = InvitedUsers(referral_code=params.referral_code,
                                      registered_user_email=params.email,
                                      referrer_id=referrer_id)
        session.add(referral_entry)

    await session.commit()

    return {"message": "Successfully!"}


@router.post("/login")
async def login(params: LoginParams, session: AsyncSession = Depends(get_session)):
    query = await session.execute(
        select(Users)
        .where(Users.email == params.email)
    )
    result = query.scalar_one_or_none()

    if not result:
        raise CustomException(detail="user_not_found", status_code=404)
    if not pwd_context.verify(params.password, result.password_hash):
        raise CustomException(detail="incorrect_name_or_password", status_code=400)

    token = make_jwt_token(params.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/referral_code")
async def create_referral_code(params: CreateReferralCodeParams,
                               user: Users = Depends(get_current_user),
                               session: AsyncSession = Depends(get_session)):
    email = user.email

    if params.end_date.timestamp() < datetime.now().timestamp():
        raise CustomException(detail="incorrect_end_date", status_code=400)

    referral_code = ReferralCodes(
        referral_code=generate_referral_code(),
        end_date=params.end_date,
        referrer_id=user.id
    )

    session.add(referral_code)
    await session.commit()
    await session.refresh(referral_code)
    return {"message": f"Referral code for {email}", "referral_code": referral_code.referral_code,
            "end_date": referral_code.end_date}


@router.delete("/referral_code")
async def delete_referral_code(user: Users = Depends(get_current_user),
                               session: AsyncSession = Depends(get_session),
                               redis_client: redis.Redis = Depends(get_redis)):
    query = await session.execute(
        select(ReferralCodes)
        .where(ReferralCodes.referrer_id == user.id)
        .order_by(ReferralCodes.id.desc())
    )
    referral_code = query.scalar()

    if not referral_code:
        raise CustomException(detail="referral_code_not_found", status_code=404)

    referral_code.is_deleted = True

    referral_code_in_cache = await redis_client.get(user.email)
    if referral_code_in_cache:
        referral_code_in_cache = json.loads(referral_code_in_cache)
        if referral_code.referral_code == referral_code_in_cache["code"]:
            await redis_client.delete(user.email)

    await session.commit()
    return {"message": "Successfully deleted"}


@router.get("/referral_code/{email}")
async def get_referral_code(email: str, session: AsyncSession = Depends(get_session),
                            redis_client: redis.Redis = Depends(get_redis)):
    cached_dict = await redis_client.get(email)
    if cached_dict:
        cached_dict = json.loads(cached_dict)
        if datetime.fromtimestamp(cached_dict["end_date"]).timestamp() < datetime.now().timestamp():
            raise CustomException(detail="active_referral_code_not_found", status_code=404)
        return {"message": "Referral code from cache", "referral_code": cached_dict["code"]}

    user_query = await session.execute(
        select(Users)
        .where(Users.email == email)
    )
    user = user_query.scalar_one_or_none()

    if not user:
        raise CustomException(detail="user_not_found", status_code=404)

    referral_code_query = await session.execute(
        select(ReferralCodes)
        .where(ReferralCodes.referrer_id == user.id)
        .order_by(ReferralCodes.id.desc())
    )
    referral_code = referral_code_query.scalar()

    if referral_code is None:
        raise CustomException(detail="active_referral_code_not_found", status_code=404)
    if referral_code.is_deleted:
        raise CustomException(detail="referral_code_is_deleted", status_code=400)

    await redis_client.set(
        email,
        json.dumps({"code": referral_code.referral_code, "end_date": referral_code.end_date.timestamp()}),
        ex=60 * 60
    )

    return {"message": "Referral code for this user", "referral_code": referral_code.referral_code}


@router.get("/user_info/{user_id}")
async def get_info(user_id: int, session: AsyncSession = Depends(get_session)):
    query = await session.execute(
        select(Users)
        .where(Users.id == user_id)
    )
    user = query.scalar_one_or_none()

    if not user:
        raise CustomException(detail="user_not_found", status_code=404)

    invited_users_query = await session.execute(
        select(Users.email, InvitedUsers.referral_code, Users.hunter_info)
        .join(Users, InvitedUsers.registered_user_email == Users.email)
        .where(InvitedUsers.referrer_id == user_id)
    )
    invited_users = [
        {
            "email": email,
            "referral_code": referral_code,
            "hunter_data": hunter_info
        }
        for email, referral_code, hunter_info in invited_users_query.all()
    ]

    user_referral_code_query = await session.execute(
        select(ReferralCodes.referral_code)
        .where(ReferralCodes.referrer_id == user_id)
        .order_by(ReferralCodes.id.desc())
    )
    user_referral_code = user_referral_code_query.scalar()
    if not user_referral_code:
        raise CustomException(detail="referral_code_not_found", status_code=404)

    return {
        "email": user.email,
        "referral_code": user_referral_code,
        "invited_users": invited_users
    }
