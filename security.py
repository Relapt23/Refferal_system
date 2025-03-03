import os

import jwt
from dotenv import load_dotenv

load_dotenv()

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


def make_jwt_token(username):
    return jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)
