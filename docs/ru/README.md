# aiogram-template

Production-ready шаблон для Telegram-ботов на aiogram 3.x.

## Быстрый старт

```bash
git clone https://github.com/qu1nqqy/aiogram_template.git aiogram_bot
cd aiogram_bot
uv sync --dev
cp config.example.toml config.toml
# отредактируй config.toml — укажи bot.token
make run
```

## Конфигурация

Приложение поддерживает три источника конфигурации (по приоритету):

1. **Переменные окружения** (высший приоритет, разделитель вложенности `__`)
2. **config.json**
3. **config.toml**

Пример: `BOT__TOKEN=123:ABC` переопределит `bot.token` из TOML.

### Секции конфигурации

| Секция | Описание |
|--------|----------|
| `[bot]` | Токен бота, debug-режим, часовой пояс, drop_pending_updates |
| `[database]` | PostgreSQL: хост, порт, логин, пароль + настройки пула соединений |
| `[redis]` | Redis: хост, порт, пароль, размер пула |
| `[s3]` | S3/MinIO: хосты (internal/external), ключи, бакет |
| `[logging]` | Уровень логирования (DEBUG/INFO/WARNING/ERROR) |

## Архитектура

```
src/
├── bot/           — слой Telegram-бота
├── core/          — инфраструктура (БД, кеш, S3, конфиг)
├── di/            — DI-контейнер (dishka)
├── models/        — SQLAlchemy-модели
├── repos/         — репозитории (sql/redis/s3)
├── services/      — бизнес-логика
├── schemas/       — DTO, enum'ы, Pydantic-схемы
└── utils/         — утилиты
```

### Слой бота (`src/bot/`)

Каждая фича оформляется как набор файлов:

- **`handlers/`** — фабрика роутеров `build_*_router() -> Router`
- **`keyboards/`** — классы клавиатур с instance-методами через `InlineKeyboardBuilder` / `ReplyKeyboardBuilder`
- **`texts/`** — классы текстов с `@classmethod`-методами
- **`states/`** — группы FSM-состояний (`StatesGroup`)

```python
# handlers/example.py
def build_start_router() -> Router:
    router = Router()
    kb = StartKeyboards()

    @router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        await message.answer(
            StartText.greeting(message.from_user.first_name),
            reply_markup=kb.main(),
        )

    return router
```

### Dependency Injection (dishka)

Три провайдера с разными скоупами:

| Провайдер | Scope | Что предоставляет |
|-----------|-------|-------------------|
| `CoreProvider` | APP | AsyncEngine, session_factory, Redis pool, Redis client |
| `RequestProvider` | REQUEST | S3 клиенты (internal/external) |
| `RepositoryProvider` | REQUEST | AsyncSession, репозитории |
| `ServiceProvider` | REQUEST | Сервисы бизнес-логики |

APP-скоуп — синглтоны на всё время жизни бота. REQUEST-скоуп — новый экземпляр на каждый update.

### Репозитории

Абстрактные интерфейсы для инфраструктурного слоя (подмена реализации в тестах):

- **`AbstractBaseRepository[ModelT]`** — CRUD для SQL (get_by_id, get_all, create, update, delete)
- **`AbstractCacheRepository`** — кеш (get, set, delete, exists, get_many, set_many)
- **`AbstractS3Repository`** — файлы (upload, download, delete, exists, presigned_url)

### Модели и миксины

- **`TimestampMixin`** — автоматические `created_at` / `updated_at`
- **`SoftDeleteMixin`** — мягкое удаление (`deleted_at`), автофильтрация SELECT-запросов

```python
class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
```

### Сессии и транзакции

Сессия создаётся через DI на каждый REQUEST с `session.begin()` — автоматический commit при успехе, rollback при исключении. Коммиты в репозиториях.

### Логирование

structlog с JSON-форматом. Контекстные переменные: `update_type`, `user_id`, `update_id`. Middleware автоматически логирует каждый входящий update и время обработки.

### Обработка ошибок

Глобальный error-роутер `@router.errors()` — логирует исключение и уведомляет пользователя.

## Docker

```bash
docker build -t my-bot .
docker run --env-file .env my-bot
```

Dockerfile: multi-stage build, non-root user, автоматические миграции при старте.

## CI/CD (GitHub Actions)

| Workflow | Триггер | Что делает |
|----------|---------|------------|
| `tests.yml` | push/PR | pytest |
| `lint.yml` | push/PR | ruff |
| `typecheck.yml` | push/PR | ty |
| `dev.yml` | push в dev | Деплой на dev-сервер |
| `main.yml` | push в main | Деплой на прод |

## Make-команды

```bash
make run              # Запуск бота
make format           # Форматирование (ruff)
make lint             # Проверка кода (ruff)
make revision         # Создать миграцию alembic
make upgrade          # Применить миграции
make test             # Unit-тесты
make test/coverage    # Тесты с покрытием
make mark             # Автоматическая расстановка pytest-маркеров
```
