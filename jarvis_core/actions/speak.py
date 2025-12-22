import logging

logger = logging.getLogger(__name__)

class Speaker:
    def __init__(self):
        pass

    def speak(self, text):
        logger.info(f"SPEAKING: {text}")
        # Implement TTS logic here
