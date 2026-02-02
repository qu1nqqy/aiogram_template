from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
	__tablename__ = "users"

	telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
	username: Mapped[str | None] = mapped_column(String(255), default=None)
	first_name: Mapped[str | None] = mapped_column(String(255), default=None)
