import logging
import asyncio
import json
from datetime import datetime
from jarvis_core.core.event_bus import EventBus
from jarvis_core.models.llm import LLM
from jarvis_core.speech.tts.piper_tts import PiperTTS
from jarvis_core.core.memory import WorkingMemory
from jarvis_core.core.ltm import LongTermMemory
from jarvis_core.core.constitution import get_constitution
from jarvis_core.core.personality import get_personality_string

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, event_bus: EventBus, llm: LLM, tts: PiperTTS, memory: WorkingMemory, ltm: LongTermMemory):
        self.event_bus = event_bus
        self.llm = llm
        self.tts = tts
        self.memory = memory
        self.ltm = ltm
        self._subscribe()

    def _subscribe(self):
        self.event_bus.subscribe("user_speech", self.on_user_speech)

    async def on_user_speech(self, event):
        # Notify that we are busy
        await self.event_bus.publish("agent_state", {"state": "busy"})
        
        # EventBus passes data directly as the argument
        payload = event 
        text = payload.get("text")
        
        logger.info(f"ConversationManager received event: {payload}") 
        
        if text:
            try:
                # 1. Log to Memory
                self.memory.add("user_command", text, meta={"source": "voice"})

                # 2. Query LLM
                logger.info(f"Step 1: Fetching context for text: {text}") 
                context_str = self.memory.get_context_string(n=10)
                
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Build system prompt using structured layers
                constitution = get_constitution()
                personality = get_personality_string()
                
                # LTM Layers
                profile_str = self.ltm.get_profile_string()
                prefs_str = self.ltm.get_preferences_string()
                habits_str = self.ltm.get_habits_string()
                
                state_summary = f"CURRENT STATE:\n- Date and Time: {now}\n- Agent State: Processing user request"
                memory_summary = f"RECENT MEMORY:\n{context_str}" if context_str else "RECENT MEMORY: None"
                
                # Combine all layers
                system_instruction = f"""{constitution}

{personality}

{profile_str}

{prefs_str}

{habits_str}

{state_summary}

{memory_summary}"""
                
                full_prompt = f"USER: {text}"
                
                logger.info("Step 2: Sending request to LLM (JSON Mode)...")
                response_data = await self.llm.chat(full_prompt, system_prompt=system_instruction)
                logger.info(f"Step 3: Received LLM response: {response_data}")

                if isinstance(response_data, dict):
                    await self._process_response(response_data)
                else:
                    logger.error(f"Invalid response format (not dict): {response_data}")
                    # Fallback speech if possible
                    if isinstance(response_data, str):
                         await asyncio.to_thread(self.tts.speak, "I encountered an error processing the response.")

            except Exception as e:
                logger.error(f"Error in on_user_speech: {e}")
            finally:
                # Notify that we are idle again
                await self.event_bus.publish("agent_state", {"state": "idle"})

    async def _process_response(self, data: dict):
        # 1. Speech
        speech = data.get("speech", {})
        if speech.get("say", False):
            text_to_speak = speech.get("text", "")
            if text_to_speak:
                # Log what we are about to say
                self.memory.add("assistant_response", text_to_speak)
                logger.info(f"Speaking: {text_to_speak}")
                await asyncio.to_thread(self.tts.speak, text_to_speak)

        # 2. Actions
        actions = data.get("actions", [])
        for action in actions:
            await self._execute_action(action)

        # 3. Memory Proposals
        proposals = data.get("memory_proposals", [])
        for proposal in proposals:
            self.ltm.process_proposal(proposal)

    async def _execute_action(self, action: dict):
        action_type = action.get("type")
        params = action.get("params", {})
        logger.info(f"EXECUTING ACTION: {action_type} with {params}")
        
        # Publish to EventBus for Executor or other components to handle
        await self.event_bus.publish("action_requested", {"type": action_type, "params": params})
