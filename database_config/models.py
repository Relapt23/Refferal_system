from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    password: Mapped[str]
    jwt: Mapped[Optional[str]] = mapped_column(nullable=True)
    referral_code: Mapped[Optional[str]] = mapped_column(nullable=True)
