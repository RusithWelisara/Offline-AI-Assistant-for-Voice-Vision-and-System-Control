import logging
import time
import os
import speech_recognition as sr
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class WhisperSTT:
    def __init__(self, model_size="tiny", device="cpu", compute_type="int8"):
        """
        Initialize WhisperSTT with faster-whisper.
        Args:
            model_size: Model size (tiny, base, small, medium, large-v2)
            device: 'cpu' or 'cuda'
            compute_type: 'int8', 'float16', etc.
        """
        logger.info(f"Loading Whisper model: {model_size} on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.recognizer = sr.Recognizer()
        logger.info("Whisper model loaded.")

    def listen_and_transcribe(self) -> dict:
        """
        Captures audio from the microphone and transcribes it.
        Returns a dict with 'text' and 'processing_time'.
        """
        with sr.Microphone() as source:
            logger.info("Adjusting for ambient noise... Please wait.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Listening... Speak now.")
            
            try:
                audio = self.recognizer.listen(source, timeout=None) # Listen until silence
                
                start_time = time.time()
                logger.info("Processing audio...")
                
                # faster-whisper works well with file paths.
                # Saving to a temporary file is a robust way to handle format.
                temp_filename = "temp_voice_input.wav"
                with open(temp_filename, "wb") as f:
                    f.write(audio.get_wav_data())
                
                segments, info = self.model.transcribe(temp_filename, beam_size=5, language="en")
                
                text_segments = []
                for segment in segments:
                    text_segments.append(segment.text)
                
                full_text = " ".join(text_segments).strip()
                
                # Cleanup
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                
                processing_time = time.time() - start_time
                logger.info(f"Transcribed: {full_text} (STT Delay: {processing_time:.2f}s)")
                
                return {
                    "text": full_text,
                    "processing_time": processing_time
                }

            except Exception as e:
                logger.error(f"Error during transcription: {e}")
                return {"text": "", "processing_time": 0}
