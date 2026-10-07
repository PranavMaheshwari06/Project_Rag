# Settings and Configuration

Applications need configuration — database URLs, API keys, feature flags —
and hardcoding them is how keys end up on GitHub. The standard pattern is to
read configuration from environment variables into a typed settings object.

## Loading configuration from environment variables

Pydantic's `BaseSettings` reads attributes from the environment, converts
them to the declared types, and fails loudly at startup if something required
is missing or malformed.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Awesome API"
    admin_email: str
    items_per_page: int = 50

settings = Settings()
```

With `ADMIN_EMAIL=ops@example.com` and `ITEMS_PER_PAGE=25` exported in the
environment, `settings.admin_email` is a validated string and
`settings.items_per_page` is the integer 25. Environment variable names are
matched case-insensitively to field names.

## Using a .env file

For local development it's easier to keep values in a `.env` file than to
export them by hand. Point the settings class at it; real environment
variables still take precedence over the file.

```python
class Settings(BaseSettings):
    admin_email: str
    database_url: str

    model_config = {"env_file": ".env"}
```

Keep `.env` out of version control — it exists precisely to hold values that
differ per machine and secrets that must never be committed.

## Settings as a dependency

Expose settings through a cached dependency instead of a module-level global.
`lru_cache` means the environment is read once, and tests can override the
dependency to inject their own settings without touching the real
environment.

```python
from functools import lru_cache
from fastapi import Depends, FastAPI

@lru_cache
def get_settings():
    return Settings()

app = FastAPI()

@app.get("/info")
def info(settings: Settings = Depends(get_settings)):
    return {"app_name": settings.app_name}
```

In tests: `app.dependency_overrides[get_settings] = lambda: Settings(admin_email="test@x.dev")`
and every endpoint sees the test values.
