from config import settings
from logger import logger

def get_llm():
    """
    Returns the configured LLM instance.
    Supports Google GenAI (Gemini) based on validated settings.
    """
    if settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,
                max_retries=5,
                streaming=True,
                convert_system_message_to_human=True,
                # Sometimes needed for older models, but harmless
            )
        except ImportError as e:
            logger.error("langchain_google_genai not installed.")
            raise e
    
    logger.warning("GEMINI_API_KEY not found in settings.")
    return None
