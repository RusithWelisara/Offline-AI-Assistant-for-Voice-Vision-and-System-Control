import logging
import sys
import os

# Add the project root to sys.path so we can import jarvis_core
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from jarvis_core.speech.tts.piper_tts import PiperTTS

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_tts():
    print("Initializing PiperTTS...")
    tts = PiperTTS()
    
    print(f"Piper binary being used: {tts.piper_binary}")
    print(f"Model path: {tts.model_path}")
    
    if os.path.exists(tts.model_path):
        size = os.path.getsize(tts.model_path)
        print(f"Model file size: {size} bytes")
        if size < 1024:
            print("ERROR: Model file is still just an LFS pointer!")
            return
    else:
        print("ERROR: Model file not found!")
        return

    test_text = "Hello, this is a test of the text to speech system. If you can hear this, the fix is working."
    print(f"Speaking: '{test_text}'")
    tts.speak(test_text)
    print("Test complete.")

if __name__ == "__main__":
    test_tts()
