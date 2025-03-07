from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database_config.db import get_session
from database_config.models import Users, InvitedUsers
from database_config.schemas import SignUp, CustomException, Login
from services.security import pwd_context, make_jwt_token, get_current_user
from services.referral_services import generate_referral_code

router = APIRouter()


@router.post("/sign_up")
async def sign_up(user: SignUp, session: AsyncSession = Depends(get_session)):
    query = await session.execute(select(Users).where(Users.email == user.email))
    result = query.scalar_one_or_none()

    if result:
        raise CustomException(detail="existing_user", status_code=400)

    hashed_password = pwd_context.hash(user.password)

    if user.referral_code:
        query2 = await session.execute(select(Users).where(Users.referral_code == user.referral_code))
        referrer = query2.scalar_one_or_none()
        if referrer is None:
            raise CustomException(detail="invalid_referral_code", status_code=400)

    new_user = Users(email=user.email, password=hashed_password)
    session.add(new_user)
    await session.commit()

    if user.referral_code:
        referral_entry = InvitedUsers(referral_code=user.referral_code, registered_user=user.email)
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


@router.get("/create_code")
async def create_referral_code(user: Users = Depends(get_current_user),
                               session: AsyncSession = Depends(get_session)):
    referral_code = generate_referral_code()
    user.referral_code = referral_code
    await session.commit()
    await session.refresh(user)
    return {"message": f"Referral code for {user.email}", "referral_code": f"{referral_code}"}


@router.get("/delete_code")
async def delete_referral_code(user: Users = Depends(get_current_user),
                               session: AsyncSession = Depends(get_session)):
    if not user.referral_code:
        raise CustomException(detail="referral_code_not_found", status_code=404)
    user.referral_code = None
    await session.commit()
    return {"message": "Successfully deleted"}


@router.get("/create_code/{email}")
async def get_referral_code(email: str, session: AsyncSession = Depends(get_session)):
    query = await session.execute(select(Users).where(Users.email == email))
    user = query.scalar_one_or_none()
    if not user:
        raise CustomException(detail="user_not_found", status_code=404)
    if user.referral_code is None:
        raise CustomException(detail="referral_code_not_found", status_code=404)
    return {"message": f"Referral code for this user", "referral_code": f"{user.referral_code}"}


@router.get("/info/{id}")
async def get_info(id: int, session: AsyncSession = Depends(get_session)):
    query = await session.execute(select(Users).where(Users.id == id))
    user = query.scalar_one_or_none()

    if not user:
        raise CustomException(detail="user_not_found", status_code=404)

    invited_users_query = await session.execute(
        select(Users.email, Users.referral_code)
        .join(InvitedUsers, Users.email == InvitedUsers.registered_user)
        .where(InvitedUsers.referral_code == user.referral_code)
    )
    invited_users = [
        {"email": email, "referral_code": referral_code}
        for email, referral_code in invited_users_query.all()
    ]

    return {
        "email": user.email,
        "referral_code": user.referral_code,
        "invited_users": invited_users
    }
