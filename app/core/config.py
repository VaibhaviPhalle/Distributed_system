from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Distributed Rate Limiter"
    DATABASE_URL: str
    REDIS_URL: str
    ADMIN_API_KEY: str
    RATE_LIMITER_FAILURE_STRATEGY: str = "fail-open"

    class Config:
        env_file = ".env"

settings = Settings()