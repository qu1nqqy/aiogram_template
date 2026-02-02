# ruff: noqa: ANN001, ANN002, ANN202, ARG002

import traceback

from aiogram import Router
from aiogram.types import ErrorEvent

from src.services.logger import get_logger

logger = get_logger()

error_router = Router(name="error_router")


@error_router.errors()
async def handle_error(event: ErrorEvent) -> None:
	"""
	Глобальный обработчик ошибок aiogram.
	Логирует исключение и при необходимости отвечает пользователю.
	"""
	logger.error(
		"Unhandled error in handler",
		error=str(event.exception),
		traceback=traceback.format_exc(),
	)

	# Попытка уведомить пользователя
	update = event.update
	if update.message:
		await update.message.answer("Произошла ошибка. Попробуйте позже.")
	elif update.callback_query:
		await update.callback_query.answer(
			"Произошла ошибка. Попробуйте позже.",
			show_alert=True,
		)
