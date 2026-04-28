import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from langfuse.langchain import CallbackHandler

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys & Models
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"
    TAVILY_API_KEY: Optional[str] = None
    
    # Langfuse
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
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
os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
langfuse_handler = CallbackHandler()

# Exportamos para manter compatibilidade com o que já existe
DB_NAME = settings.DB_NAME
