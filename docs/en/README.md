# aiogram-template

Production-ready template for Telegram bots built with aiogram 3.x.

## Quick start

```bash
git clone https://github.com/qu1nqqy/aiogram_template.git aiogram_bot
cd aiogram_bot
uv sync --dev
cp config.example.toml config.toml
# edit config.toml — set bot.token
make run
```

## Configuration

The app supports three config sources (by priority):

1. **Environment variables** (highest priority, nesting delimiter `__`)
2. **config.json**
3. **config.toml**

Example: `BOT__TOKEN=123:ABC` overrides `bot.token` from TOML.

### Config sections

| Section | Description |
|---------|-------------|
| `[bot]` | Bot token, debug mode, timezone, drop_pending_updates |
| `[database]` | PostgreSQL: host, port, credentials + connection pool tuning |
| `[redis]` | Redis: host, port, password, pool size |
| `[s3]` | S3/MinIO: hosts (internal/external), keys, bucket |
| `[logging]` | Log level (DEBUG/INFO/WARNING/ERROR) |

## Architecture

```
src/
├── bot/           — Telegram bot layer
├── core/          — Infrastructure (DB, cache, S3, config)
├── di/            — DI container (dishka)
├── models/        — SQLAlchemy models
├── repos/         — Repositories (sql/redis/s3)
├── services/      — Business logic
├── schemas/       — DTOs, enums, Pydantic schemas
└── utils/         — Utilities
```

### Bot layer (`src/bot/`)

Each feature is organized as a set of files:

- **`handlers/`** — router factories `build_*_router() -> Router`
- **`keyboards/`** — keyboard classes with instance methods using `InlineKeyboardBuilder` / `ReplyKeyboardBuilder`
- **`texts/`** — text classes with `@classmethod` methods
- **`states/`** — FSM state groups (`StatesGroup`)

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

Three providers with different scopes:

| Provider | Scope | Provides |
|----------|-------|----------|
| `CoreProvider` | APP | AsyncEngine, session_factory, Redis pool, Redis client |
| `RequestProvider` | REQUEST | S3 clients (internal/external) |
| `RepositoryProvider` | REQUEST | AsyncSession, repositories |
| `ServiceProvider` | REQUEST | Business logic services |

APP scope — singletons for the entire bot lifetime. REQUEST scope — new instance per update.

### Repositories

Abstract interfaces for the infrastructure layer (swappable in tests):

- **`AbstractBaseRepository[ModelT]`** — SQL CRUD (get_by_id, get_all, create, update, delete)
- **`AbstractCacheRepository`** — cache (get, set, delete, exists, get_many, set_many)
- **`AbstractS3Repository`** — files (upload, download, delete, exists, presigned_url)

### Models & mixins

- **`TimestampMixin`** — automatic `created_at` / `updated_at`
- **`SoftDeleteMixin`** — soft delete (`deleted_at`), automatic SELECT filtering

```python
class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
```

### Sessions & transactions

Session is created via DI per REQUEST with `session.begin()` — auto-commit on success, rollback on exception. Commits happen in repositories.

### Logging

structlog with JSON output. Context variables: `update_type`, `user_id`, `update_id`. Middleware automatically logs each incoming update and processing time.

### Error handling

Global error router `@router.errors()` — logs the exception and notifies the user.

## Docker

```bash
docker build -t my-bot .
docker run --env-file .env my-bot
```

Dockerfile: multi-stage build, non-root user, automatic migrations on startup.

## CI/CD (GitHub Actions)

| Workflow | Trigger | Action |
|----------|---------|--------|
| `tests.yml` | push/PR | pytest |
| `lint.yml` | push/PR | ruff |
| `typecheck.yml` | push/PR | ty |
| `dev.yml` | push to dev | Deploy to dev server |
| `main.yml` | push to main | Deploy to production |

## Make targets

```bash
make run              # Start bot
make format           # Format code (ruff)
make lint             # Check code (ruff)
make revision         # Create alembic migration
make upgrade          # Apply migrations
make test             # Unit tests
make test/coverage    # Tests with coverage report
make mark             # Auto-assign pytest markers
```
