# ruff: noqa: ANN001, ANN002, ANN202, ARG001, ANN401
from __future__ import annotations

from contextvars import ContextVar
from typing import Any, cast

import structlog

from src.core.config import cfg

# Контекстные переменные для update'ов бота
update_type: ContextVar[str] = ContextVar("update_type", default="")
user_id: ContextVar[int | None] = ContextVar("user_id", default=None)
update_id: ContextVar[str] = ContextVar("update_id", default="")


def bot_context_processor(
	logger: Any,
	method_name: str,
	event_dict: dict[str, Any],
) -> dict[str, Any]:
	"""Добавляет контекст бота в логи."""
	_update_type = update_type.get("")
	_user_id = user_id.get(None)
	_update_id = update_id.get("")

	if _update_type:
		event_dict["update_type"] = _update_type
	if _user_id is not None:
		event_dict["user_id"] = _user_id
	if _update_id:
		event_dict["update_id"] = _update_id

	return event_dict


def reorder_keys_processor(
	logger: Any,
	method_name: str,
	event_dict: dict[str, Any],
) -> dict[str, Any]:
	"""Ставит update_type/user_id в начало JSON-лога."""
	ordered_dict: dict[str, Any] = {}

	if "update_type" in event_dict:
		ordered_dict["update_type"] = event_dict.pop("update_type")
	if "user_id" in event_dict:
		ordered_dict["user_id"] = event_dict.pop("user_id")
	if "update_id" in event_dict:
		ordered_dict["update_id"] = event_dict.pop("update_id")

	ordered_dict.update(event_dict)
	return ordered_dict


def configure_logger() -> None:
	log_level = cfg.logging.level.upper()
	allowed_levels = {
		"DEBUG": 10,
		"INFO": 20,
		"WARNING": 30,
		"ERROR": 40,
		"CRITICAL": 50,
	}
	log_level = allowed_levels.get(log_level, 20)
	structlog.configure_once(
		processors=cast(Any, [
			structlog.contextvars.merge_contextvars,
			bot_context_processor,
			structlog.processors.add_log_level,
			structlog.dev.set_exc_info,
			structlog.processors.TimeStamper(),
			reorder_keys_processor,
			structlog.processors.JSONRenderer(),
		]),
		context_class=dict,
		logger_factory=structlog.PrintLoggerFactory(),
		cache_logger_on_first_use=False,
		wrapper_class=structlog.make_filtering_bound_logger(log_level),
	)


class StructLogger:
	def __init__(self, context: dict[str, Any] | None = None) -> None:
		self._logger = None
		self._context = context or {}

	def _get_logger(self) -> Any:
		if self._logger is None:
			self._logger = structlog.get_logger()
		return self._logger

	def _get_caller_info(self) -> dict[str, Any]:
		import inspect

		stack = inspect.stack()
		for frame_info in stack[2:]:
			if (
				"logger.py" not in frame_info.filename
				and "structlog" not in frame_info.filename
			):
				return {
					"source_file": frame_info.filename.split("/")[-1],
					"func_name": frame_info.function,
					"lineno": frame_info.lineno,
					"pathname": frame_info.filename,
				}

		return {}

	def debug(self, message: str, **kwargs: object) -> None:
		caller_info = self._get_caller_info()
		self._get_logger().bind(**self._context, **caller_info).debug(
			message,
			**kwargs,
		)

	def info(self, message: str, **kwargs: object) -> None:
		caller_info = self._get_caller_info()
		self._get_logger().bind(**self._context, **caller_info).info(
			message,
			**kwargs,
		)

	def warning(self, message: str, **kwargs: object) -> None:
		caller_info = self._get_caller_info()
		self._get_logger().bind(**self._context, **caller_info).warning(
			message,
			**kwargs,
		)

	def error(self, message: str, **kwargs: object) -> None:
		caller_info = self._get_caller_info()
		self._get_logger().bind(**self._context, **caller_info).error(
			message,
			**kwargs,
		)

	def critical(self, message: str, **kwargs: object) -> None:
		caller_info = self._get_caller_info()
		self._get_logger().bind(**self._context, **caller_info).critical(
			message,
			**kwargs,
		)

	def bind(self, **kwargs: object) -> "StructLogger":
		new_context = {**self._context, **kwargs}
		return StructLogger(new_context)


_logger_instance: StructLogger | None = None


def get_logger() -> StructLogger:
	global _logger_instance
	if _logger_instance is None:
		configure_logger()
		_logger_instance = StructLogger()
	return _logger_instance
