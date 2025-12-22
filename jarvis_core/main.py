import asyncio
import logging
import sys
import os
from pydub import AudioSegment
from pydub.playback import play

# Add parent directory to path to allow running as script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis_core.config import Config
from jarvis_core.core.event_bus import EventBus
from jarvis_core.core.autonomy_loop import AutonomyLoop

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def play_startup_sound():
    sound_path = "d:\\AI Assistant\\JARVIS\\jarvis_core\\Assests\\wake_word_detected.mp3"
    if os.path.exists(sound_path):
        sound = AudioSegment.from_mp3(sound_path)
        play(sound)
    else:
        logger.warning(f"Startup sound file not found: {sound_path}")

async def main():
    logger.info("Starting Jarvis Core...")
    play_startup_sound() # Play sound at startup
    
    # Initialize basic components
    config = Config()
    event_bus = EventBus()
    
    # Initialize Autonomy Loop
    autonomy = AutonomyLoop(event_bus)
    
    # Start the loop
    try:
        await autonomy.start()
    except KeyboardInterrupt:
        logger.info("Stopping Jarvis Core...")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
