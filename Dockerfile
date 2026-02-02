# =============================================================================
# Dockerfile для aiogram template
# Multi-stage build для минимизации размера итогового образа
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - установка зависимостей
# -----------------------------------------------------------------------------
FROM python:3.12.8-slim-bookworm AS builder

# Устанавливаем uv для быстрой установки зависимостей
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install uv

WORKDIR /app

# Копируем только файлы, необходимые для установки зависимостей
# Это позволяет кэшировать слой с зависимостями при изменении кода
COPY pyproject.toml uv.lock README.md ./

# Устанавливаем зависимости с кэшированием
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# -----------------------------------------------------------------------------
# Stage 2: Runtime - минимальный образ для запуска
# -----------------------------------------------------------------------------
FROM python:3.12.8-slim-bookworm AS runtime

# Метаданные образа
LABEL maintainer="qu1nqqy" \
      description="aiogram template"

# Переменные окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Создаём непривилегированного пользователя для безопасности
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Копируем виртуальное окружение из builder stage
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Копируем pyproject.toml (содержит конфигурацию alembic)
COPY pyproject.toml ./

# Копируем миграции базы данных
COPY migrations ./migrations

# Копируем исходный код приложения
COPY src ./src

# Копируем конфигурацию приложения
COPY config.toml ./

# Устанавливаем владельца файлов
RUN chown -R appuser:appgroup /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Запуск: сначала миграции, затем бот
CMD ["sh", "-c", "alembic upgrade head && python -m src"]
