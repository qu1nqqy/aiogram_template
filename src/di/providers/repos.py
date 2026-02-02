from collections.abc import AsyncGenerator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.repos.sql.interfaces import AbstractBaseRepository


class RepositoryProvider(Provider):
	scope = Scope.REQUEST  # Новый на каждый хендлер

	@provide
	async def get_session(
		self,
		factory: async_sessionmaker[AsyncSession],
	) -> AsyncGenerator[AsyncSession, None]:
		async with factory() as session:
			async with session.begin():
				yield session

	@provide
	def get_user_repo(self, session: AsyncSession) -> AbstractBaseRepository:
		return AbstractBaseRepository(session)
