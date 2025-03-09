from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey
from sqlalchemy import JSON


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    referral_code: Mapped[Optional[str]] = mapped_column(nullable=True)
    hunter_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class InvitedUsers(Base):
    __tablename__ = "invited_users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    referral_code: Mapped[Optional[str]] = mapped_column(nullable=True)
    registered_user_email: Mapped[str] = mapped_column(ForeignKey("users.email"), nullable=True)
