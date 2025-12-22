import sounddevice as sd
import numpy as np
import time
import os
from openwakeword.model import Model
from pydub import AudioSegment
from pydub.playback import play

class WakeWordDetector:
    def __init__(
        self,
        model_paths,
        threshold=0.6,
        sample_rate=16000,
        chunk_size=1280,
        cooldown=2.0
    ):
        # Allow passing just names if model is in cache, or paths
        self.model = Model(wakeword_models=model_paths)
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.cooldown = cooldown
        self.last_trigger_time = 0
        self.wake_word_sound_path = "d:\\AI Assistant\\JARVIS\\jarvis_core\\Assests\\wake_word_detected.mp3"
        self.is_running = False

    def _cooldown_ok(self):
        return (time.time() - self.last_trigger_time) > self.cooldown

    def play_wake_word_sound(self):
        if os.path.exists(self.wake_word_sound_path):
            sound = AudioSegment.from_mp3(self.wake_word_sound_path)
            play(sound)
        else:
            print(f"Wake word sound file not found: {self.wake_word_sound_path}")

    def listen(self, on_detect):
        """
        Listens for wake word. 
        Calls on_detect(wakeword, confidence) when detected.
        Wait... if we want to run STT, we need to STOP listening.
        So this method will block until detection, then return, unless on_detect tells it to continue?
        
        To allow main loop to run STT, we can design this to return upon detection.
        Or simpler: The loop inside runs until detection, then exits.
        
        Refactored from user snippet to release mic on detection.
        """
        self.is_running = True
        self.detected_event = None

        def audio_callback(indata, frames, time_info, status):
            if status:
                print(status)
            
            if not self.is_running:
                return

            audio = np.frombuffer(indata, dtype=np.int16)

            # openwakeword inference
            preds = self.model.predict(audio)
            
            for wakeword, confidence in preds.items():
                if confidence > self.threshold and self._cooldown_ok():
                    self.last_trigger_time = time.time()
                    self.play_wake_word_sound() # Play sound when wake word is detected
                    # Trigger detection
                    if on_detect:
                        on_detect(wakeword, confidence)
                    
                    # Store result to break loop
                    self.detected_event = (wakeword, confidence)
                    self.is_running = False

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            dtype="int16",
            channels=1,
            callback=audio_callback
        ):
            while self.is_running:
                time.sleep(0.05)
                
        return self.detected_event
