import logging
import os

logger = logging.getLogger(__name__)

class SystemHandler:
    def __init__(self):
        pass

    def run_command(self, cmd):
        logger.info(f"Running system command: {cmd}")
        # os.system(cmd) # Be careful with this
