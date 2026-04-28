import os
from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler

load_dotenv()

# Configurações do Langfuse
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "http://localhost:3031")
langfuse_handler = CallbackHandler()

# Configurações do Banco de Dados
DB_NAME = "checkpoints.sqlite"
