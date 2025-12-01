from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Default to localhost for local dev, but overrideable via env vars
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Other settings can go here
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    OPENAI_API_KEY: str = ""
    N8N_WEBHOOK_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
