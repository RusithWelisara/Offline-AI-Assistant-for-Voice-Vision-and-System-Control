import logging
import time
import os
import shutil
import subprocess
import urllib.request
import sys
import soundfile as sf
import sounddevice as sd
import numpy as np

logger = logging.getLogger(__name__)

class PiperTTS:
    def __init__(self, model_name="en_US-lessac-medium"):
        self.model_name = model_name
        self.models_dir = os.path.join(os.path.dirname(__file__), "models")
        self.model_path = os.path.join(self.models_dir, f"{model_name}.onnx")
        self.config_path = os.path.join(self.models_dir, f"{model_name}.onnx.json")
        self.piper_binary = "piper" # Assumes in PATH
        
        self.ensure_model()
        self.verify_binary()

    def verify_binary(self):
        if shutil.which(self.piper_binary):
            return True
            
        # Try common paths relative to python executable
        python_dir = os.path.dirname(sys.executable)
        possible_paths = [
            os.path.join(python_dir, "Scripts", "piper.exe"),
            os.path.join(python_dir, "piper.exe"),
            os.path.join(python_dir, "bin", "piper"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.piper_binary = path
                logger.info(f"Found piper binary at {path}")
                return True
                
        logger.warning("Piper binary not found in PATH or Python Scripts! TTS will likely fail.")
        return False

    def ensure_model(self):
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)

        # Integrity check: model files < 1KB are likely Git LFS pointers or failed downloads
        for path in [self.model_path, self.config_path]:
            if os.path.exists(path) and os.path.getsize(path) < 1024:
                logger.warning(f"File {path} is suspiciously small ({os.path.getsize(path)} bytes). Deleting for re-download.")
                os.remove(path)

        if not os.path.exists(self.model_path) or not os.path.exists(self.config_path):
            logger.info(f"Downloading Piper model: {self.model_name}...")
            base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium"
            
            try:
                # Download .onnx
                url = f"{base_url}/{self.model_name}.onnx"
                logger.info(f"Fetching {url}")
                urllib.request.urlretrieve(url, self.model_path)
                
                # Download .onnx.json
                url_config = f"{base_url}/{self.model_name}.onnx.json"
                logger.info(f"Fetching {url_config}")
                urllib.request.urlretrieve(url_config, self.config_path)
                
                logger.info("Piper model downloaded.")
            except Exception as e:
                logger.error(f"Failed to download Piper model: {e}")

    def speak(self, text: str):
        if not text: return

        # Command: echo "text" | piper --model ... --output-raw | (play with sounddevice)
        # Actually piper --output_raw writes raw PCM. It's safer to use WAV output to stdout and read it.
        # But piping stdout to soundfile is tricky in python.
        # Temp file approach is robust.
        
        temp_wav = "temp_tts_output.wav"
        
        start_gen = time.time()
        
        try:
            cmd = [
                self.piper_binary,
                "--model", self.model_path,
                "--output_file", temp_wav
            ]
            
            # Piper reads from stdin
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(input=text.encode('utf-8'))
            
            gen_time = time.time() - start_gen
            logger.info(f"TTS Generation Delay: {gen_time:.2f}s")
            
            if process.returncode != 0:
                logger.error(f"Piper TTS Error: {stderr.decode('utf-8')}")
                return

            start_play = time.time()
            if os.path.exists(temp_wav):
                data, fs = sf.read(temp_wav)
                sd.play(data, fs)
                sd.wait() # Wait for playback to finish
                
                play_time = time.time() - start_play
                logger.debug(f"TTS Playback took {play_time:.2f}s")
                
                # cleanup
                os.remove(temp_wav)
                
        except Exception as e:
            logger.error(f"TTS Execution failed: {e}")
