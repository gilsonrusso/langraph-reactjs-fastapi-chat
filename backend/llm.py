import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")


def get_llm():
    """
    Returns the configured LLM instance.
    Supports both Ollama and Google GenAI (Gemini) based on configuration.
    """
    if GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GEMINI_API_KEY,
                temperature=0.3,
                max_retries=5,
                streaming=True,
                convert_system_message_to_human=True,  # Sometimes needed for older models, but harmless
            )
        except ImportError:
            print("WARNING: langchain_google_genai not installed. Fallback to Ollama?")
            raise
