from fastapi import HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LoginParams(BaseModel):
    email: EmailStr
    password: str


class SignUpParams(BaseModel):
    email: EmailStr
    password: str
    referral_code: Optional[str] = None


class CreateReferralCodeParams(BaseModel):
    end_date: datetime


class CustomException(HTTPException):
    def __init__(self, detail: str, status_code: int):
        super().__init__(status_code=status_code, detail=detail)
