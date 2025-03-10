from typing import Optional
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey, JSON, DateTime


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    hunter_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class InvitedUsers(Base):
    __tablename__ = "invited_users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    referral_code: Mapped[Optional[str]] = mapped_column(nullable=True)
    registered_user_email: Mapped[str] = mapped_column(ForeignKey("users.email"), nullable=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)


class ReferralCodes(Base):
    __tablename__ = "referral_codes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    referral_code: Mapped[Optional[str]]
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(default=False)
