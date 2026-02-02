import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from src.services.logger import get_logger


class LoggingMiddleware(BaseMiddleware):
	"""Middleware для логирования входящих update'ов aiogram."""

	async def __call__(
		self,
		handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: dict[str, Any],
	) -> Any:
		logger = get_logger()
		start_time = time.time()

		update_type = "unknown"
		user_id = None

		if isinstance(event, Update):
			if event.message:
				update_type = "message"
				user_id = event.message.from_user.id if event.message.from_user else None
			elif event.callback_query:
				update_type = "callback_query"
				user_id = event.callback_query.from_user.id
			elif event.inline_query:
				update_type = "inline_query"
				user_id = event.inline_query.from_user.id

		logger.debug(
			"Update received",
			update_type=update_type,
			user_id=user_id,
		)

		try:
			result = await handler(event, data)
			process_time = time.time() - start_time
			logger.info(
				"Update handled",
				update_type=update_type,
				user_id=user_id,
				process_time_seconds=round(process_time, 4),
			)
			return result
		except Exception:
			raise
