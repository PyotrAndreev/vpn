import logging
from .app.configs.logs import setup_logging


setup_logging()

logger = logging.getLogger(__name__)
logger.debug("📝 Loggers initialized. 🚀 Program started.")
