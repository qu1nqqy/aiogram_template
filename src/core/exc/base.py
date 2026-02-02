class AppError(Exception):
	"""Базовое исключение приложения."""

	def __init__(self, message: str = "Внутренняя ошибка") -> None:
		self.message = message
		super().__init__(message)
