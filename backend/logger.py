import logging
from rich.logging import RichHandler

def setup_logger(name: str = "backend"):
    """Configura um logger estruturado e visualmente amigável."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)]
    )
    
    logger = logging.getLogger(name)
    return logger

# Instância global do logger
logger = setup_logger()
