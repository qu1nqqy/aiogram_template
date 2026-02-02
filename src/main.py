from aiogram import Bot, Dispatcher
from dishka.integrations.aiogram import setup_dishka

from src.core.config import cfg
from src.core.exc.handlers import error_router
from src.core.middlewares.logging import LoggingMiddleware
from src.di.container import get_container
from src.services.logger import get_logger


async def main() -> None:
	logger = get_logger()

	bot = Bot(token=cfg.bot.token)
	dp = Dispatcher()

	# Middleware
	dp.update.outer_middleware(LoggingMiddleware())

	# Error handler
	dp.include_router(error_router)

	# Handlers
	from src.bot.handlers import router
	dp.include_router(router)

	# DI
	container = get_container()
	setup_dishka(container=container, router=dp)

	logger.info("Bot starting...")

	try:
		await dp.start_polling(
			bot,
			drop_pending_updates=cfg.bot.drop_pending_updates,
		)
	finally:
		await container.close()
		await bot.session.close()
		logger.info("Bot stopped.")
