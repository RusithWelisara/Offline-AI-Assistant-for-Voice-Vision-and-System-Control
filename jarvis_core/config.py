import os

class Config:
    def __init__(self):
        self.MODEL_NAME = "llama3.2:3b" # Example model
        self.DEBUG = True
        self.MEMORY_DB_PATH = os.path.join(os.getcwd(), "memory.db")
        
        # Add other config paths and flags here
        
    def get(self, key, default=None):
        return getattr(self, key, default)
