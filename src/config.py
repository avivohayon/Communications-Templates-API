import logging
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic-settings for automatic validation and type conversion.
    Loads from .env file automatically.
    """
    # Database Configuration
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # SendGrid Configuration (Email)
    SENDGRID_API_KEY: str
    SENDGRID_FROM_EMAIL: str
    
    # Twilio Configuration (SMS)
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_FROM_NUMBER: str
    
    # Application Configuration
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    
    # Rate Limiting
    MAX_MESSAGES_PER_RECIPIENT_PER_HOUR: int = 5
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()


def setup_logging():
    """
    Configure Python logging based on LOG_LEVEL from settings.
    
    LOG_LEVEL options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce noise from libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    return logger
