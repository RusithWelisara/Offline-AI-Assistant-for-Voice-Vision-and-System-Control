import logging

logger = logging.getLogger(__name__)

class MicListener:
    def __init__(self, event_bus):
        self.event_bus = event_bus

    async def start_listening(self):
        logger.info("MicListener started (placeholder).")
        # Implement speech recognition logic here
        pass
