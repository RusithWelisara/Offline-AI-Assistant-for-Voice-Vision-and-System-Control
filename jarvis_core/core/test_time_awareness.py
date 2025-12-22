import asyncio
import logging
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from jarvis_core.core.conversation import ConversationManager
from jarvis_core.core.event_bus import EventBus
from jarvis_core.models.llm import LLM
from jarvis_core.speech.tts.piper_tts import PiperTTS
from jarvis_core.core.memory import WorkingMemory

logging.basicConfig(level=logging.INFO)

async def test_time_injection():
    print("Starting Time Injection Test...")
    
    # Mock dependencies
    event_bus = MagicMock(spec=EventBus)
    llm = MagicMock(spec=LLM)
    llm.chat_plain = AsyncMock(return_value="It is currently [TIME].")
    llm.chat = AsyncMock(return_value={"tasks": [], "preferences": {}})
    
    tts = MagicMock(spec=PiperTTS)
    memory = MagicMock(spec=WorkingMemory)
    memory.get_context_string.return_value = "User asked about time."
    
    # Initialize Manager
    manager = ConversationManager(event_bus, llm, tts, memory)
    
    # Simulate user speech event
    event_data = {"text": "What time is it?"}
    await manager.on_user_speech(event_data)
    
    # Verify LLM was called with time context
    args, kwargs = llm.chat_plain.call_args
    prompt = args[0]
    system_prompt = kwargs['system_prompt']
    
    print(f"\nCaptured System Prompt:\n{system_prompt}")
    
    assert "The current date and time is" in system_prompt
    print("\nSUCCESS: Current date and time found in system prompt.")
    
    # Verify intelligence extraction prompt
    await manager._extract_intelligence()
    args, _ = llm.chat.call_args
    extraction_prompt = args[0]
    
    print(f"\nCaptured Intelligence Extraction Prompt:\n{extraction_prompt[:100]}...")
    assert "The current date and time is" in extraction_prompt
    print("SUCCESS: Current date and time found in extraction prompt.")

if __name__ == "__main__":
    asyncio.run(test_time_injection())
