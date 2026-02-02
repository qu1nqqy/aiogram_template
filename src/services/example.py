from src.models.base import Base
from src.repos.redis.interfaces import AbstractCacheRepository
from src.repos.s3.interfaces import AbstractS3Repository
from src.repos.sql.interfaces import AbstractBaseRepository


class ExampleService:
	def __init__(
		self,
		sql_repo: AbstractBaseRepository,
		redis_repo: AbstractCacheRepository,
		s3_repo: AbstractS3Repository,
	) -> None:
		self.sql_repo = sql_repo
		self.cache = redis_repo
		self.photos = s3_repo

	async def get_base_with_cache(
		self,
		telegram_id: int,
	) -> Base | None:
		# Проверяем кеш
		cache_key = f"base:{telegram_id}"
		cached = await self.cache.get(cache_key)

		if cached:
			# TODO: десериализовать из JSON
			pass

		# Идем в БД
		base = await self.sql_repo.get_by_id(telegram_id)

		if base:
			# Кешируем на 5 минут
			# TODO: сериализовать в JSON
			await self.cache.set(cache_key, "{}", ttl=300)

		return base

	async def create_base_with_photo(
		self,
		telegram_id: int,
		first_name: str,
		photo_data: bytes,
	) -> Base:
		# Создаем пользователя
		base = await self.sql_repo.create(
			telegram_id=telegram_id,
			first_name=first_name,
		)

		# Загружаем фото
		photo_id = f"base/{base.id}/photo.jpg"
		await self.photos.upload_file(photo_data, photo_id)

		return base

	async def invalidate_base_cache(self, telegram_id: int) -> None:
		cache_key = f"base{telegram_id}"
		await self.cache.delete(cache_key)