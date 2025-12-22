import logging
import asyncio
import time
import threading
import openwakeword.utils
from jarvis_core.speech.wakeword.openwakeword_detector import WakeWordDetector
from jarvis_core.speech.stt.whisper_stt import WhisperSTT
from jarvis_core.core.event_bus import EventBus

logger = logging.getLogger(__name__)

class VoiceInterface:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.detector = None
        self.stt = None
        self.running = False
        self.main_loop = asyncio.get_event_loop() # Capture the main loop
        self.busy = False  # Track if agent is busy (TTS playing)
        self.busy_lock = threading.Lock()  # Thread-safe access to busy flag
        self._initialize_components()
        self._subscribe()

    def _initialize_components(self):
        max_retries = 3
        for i in range(max_retries):
            try:
                logger.info(f"Initializing Voice Components (Attempt {i+1}/{max_retries})...")
                # Ensure standard models are available
                # Note: fast-whisper also downloads on first use if not present
                openwakeword.utils.download_models() 
                
                self.detector = WakeWordDetector(model_paths=["hey_jarvis"], threshold=0.5)
                self.stt = WhisperSTT(model_size="tiny")
                logger.info("Voice Components Initialized.")
                return
            except Exception as e:
                logger.error(f"Failed to initialize voice components: {e}")
                if i < max_retries - 1:
                    logger.info("Retrying in 2 seconds...")
                    time.sleep(2)
        
        logger.error("Voice components failed to initialize after retries. Voice features disabled.")

    def _subscribe(self):
        """Subscribe to agent_state events to track busy/idle state."""
        self.event_bus.subscribe("agent_state", self.on_agent_state)

    def on_agent_state(self, event):
        """Handle agent_state events (sync callback for thread safety)."""
        state = event.get("state")
        if state:
            with self.busy_lock:
                self.busy = (state == "busy")
            logger.debug(f"VoiceInterface: Agent state changed to '{state}', busy={self.busy}")

    def _is_busy(self):
        """Thread-safe check if agent is busy."""
        with self.busy_lock:
            return self.busy

    def start(self):
        """
        Starts the voice loop in a blocking manner. 
        Should be run in a separate thread.
        """
        if not self.detector or not self.stt:
            logger.error("Voice components not initialized. Cannot start.")
            return

        self.running = True
        logger.info("Voice Interface Started. Listening...")

        def on_wake(word, confidence):
            logger.info(f"Wake word detected: {word} ({confidence:.2f})")

        while self.running:
            try:
                # Skip listening if agent is busy (TTS playing)
                if self._is_busy():
                    logger.debug("VoiceInterface: Skipping wake word detection (agent busy)")
                    time.sleep(0.5)  # Short sleep to avoid busy-waiting
                    continue
                
                # 1. Listen for Wake Word (Blocking)
                self.detector.listen(on_wake)
                
                # 2. Check again before transcribing (in case state changed during wake word detection)
                if not self.running: break
                if self._is_busy():
                    logger.debug("VoiceInterface: Skipping transcription (agent busy)")
                    continue
                
                # 3. Transcribe (Blocking)
                text = self.stt.listen_and_transcribe()
                
                if text:
                    logger.info(f"User said: {text}")
                    # Push event to bus via main loop safely
                    asyncio.run_coroutine_threadsafe(
                        self.event_bus.publish("user_speech", {"text": text, "source": "voice"}),
                        self.main_loop
                    )
            
            except Exception as e:
                logger.error(f"Error in Voice Loop: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
        if self.detector:
            self.detector.is_running = False
