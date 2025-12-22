import logging
import os
import sys
import openwakeword.utils

# Ensure jarvis_core is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis_core.speech.wakeword.openwakeword_detector import WakeWordDetector
from jarvis_core.speech.stt.whisper_stt import WhisperSTT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Ensure standard models are available
    logger.info("Checking OpenWakeWord models...")
    openwakeword.utils.download_models() # Downloads to default cache if missing

    try:
        logger.info("Initializing Wake Word Detector (OpenWakeWord)...")
        # Use 'hey_jarvis' which is a standard model name in openwakeword
        wakeword_model_names = ["hey_jarvis"] 
        # Note: If you have a specific file, you can pass the path, e.g. ["models/jarvis.onnx"]
        
        detector = WakeWordDetector(model_paths=wakeword_model_names, threshold=0.5)
        
        logger.info("Initializing Speech-to-Text (Whisper)...")
        stt = WhisperSTT(model_size="tiny")

        print("\n\033[92mJARVIS is running! Say 'Hey Jarvis' to trigger.\033[0m\n")

        def on_wake(word, confidence):
            print(f"\n\033[96mWake word '{word}' detected ({confidence:.2f})!\033[0m")

        while True:
            # 1. Wait for wake word (blocks until detection)
            # The modified listener returns upon detection to release the mic
            detector.listen(on_wake)
            
            # 2. Transcribe speech
            # Mic is released now, so STT can use it
            text = stt.listen_and_transcribe()
            
            if text:
                print(f"\033[93mYou said: {text}\033[0m")
            else:
                print("No speech detected.")

    except KeyboardInterrupt:
        logger.info("Stopping...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
