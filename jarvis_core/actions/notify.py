import logging

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self):
        pass

    def notify(self, message):
        logger.info(f"NOTIFICATION: {message}")
        # Implement actual notification logic (OS notification, etc.)
