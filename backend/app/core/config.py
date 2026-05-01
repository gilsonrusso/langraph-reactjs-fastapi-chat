import os

from langfuse.langchain import CallbackHandler
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    # API Keys & Models
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"
    TAVILY_API_KEY: str | None = None

    # Langfuse
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str = "http://localhost:3031"

    # Database
    DB_NAME: str = "checkpoints.sqlite"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = False


# Instância global de configurações
settings = Settings()

# Configuração do Langfuse
if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
    langfuse_handler = CallbackHandler()
else:
    langfuse_handler = None

# Exportamos para manter compatibilidade com o que já existe
DB_NAME = settings.DB_NAME
