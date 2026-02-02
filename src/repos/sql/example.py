from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import Base
from .interfaces import AbstractBaseRepository, ModelT


class ExampleSQLRepository(AbstractBaseRepository[Base]):
	"""
	Пример SQL репозитория для работы с БД.
	Наследуется от BaseRepository для базовых CRUD операций.
	"""

	def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
		self.session = session
		self.model = model

	async def get_by_telegram_id(self, telegram_id: int) -> User | None:
		"""
		Пример кастомного метода для поиска по telegram_id.

		:param telegram_id: ID пользователя в Telegram
		:return: User или None
		"""
		result = await self.session.execute(
			select(Base).where(Base.telegram_id == telegram_id),
		)
		return result.scalar_one_or_none()

	async def exists_by_username(self, username: str) -> bool:
		"""
		Пример проверки существования записи.

		:param username: Username пользователя
		:return: True если существует
		"""
		result = await self.session.execute(
			select(Base.id).where(Base.username == username),
		)
		return result.scalar_one_or_none() is not None
