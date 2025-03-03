from fastapi import HTTPException
from pydantic import BaseModel


class Login(BaseModel):
    username: str
    password: str


class SignUp(BaseModel):
    username: str
    password: str


class CustomException(HTTPException):
    def __init__(self, detail: str, status_code: int):
        super().__init__(status_code=status_code, detail=detail)
