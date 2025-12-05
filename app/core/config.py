from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Default to localhost for local dev, but overrideable via env vars
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Other settings can go here
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    OPENAI_API_KEY: str = ""
    N8N_WEBHOOK_URL: str = ""
    SENTRY_DSN: str = ""
    
    # LangFuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    
    # Security
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" # Generated for dev
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days (Simple strategy)
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:8501", "http://localhost:3000"] # Streamlit default port

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
