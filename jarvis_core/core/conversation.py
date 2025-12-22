import logging
import asyncio
from datetime import datetime
from jarvis_core.core.event_bus import EventBus
from jarvis_core.models.llm import LLM
from jarvis_core.speech.tts.piper_tts import PiperTTS
from jarvis_core.core.memory import WorkingMemory
from jarvis_core.core.constitution import get_constitution
from jarvis_core.core.personality import get_personality_string
from jarvis_core.core.user_profile import get_user_profile_string

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, event_bus: EventBus, llm: LLM, tts: PiperTTS, memory: WorkingMemory):
        self.event_bus = event_bus
        self.llm = llm
        self.tts = tts
        self.memory = memory
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
                
                # Build system prompt using structured layers (as per architecture)
                # Layer 1: Constitution (foundation)
                constitution = get_constitution()
                
                # Layer 2: Personality Parameters (behavioral constraints)
                personality = get_personality_string()
                
                # Layer 3: Personal Profile (contextual identity)
                user_profile = get_user_profile_string()
                
                # Layer 4: Current State Summary
                state_summary = f"CURRENT STATE:\n- Date and Time: {now}\n- Agent State: Processing user request"
                
                # Layer 5: Relevant Memory Summary
                memory_summary = f"RECENT MEMORY:\n{context_str}" if context_str else "RECENT MEMORY: None"
                
                # Combine all layers
                system_instruction = f"""{constitution}

{personality}

{user_profile}

{state_summary}

{memory_summary}

Remember: You reason. The system decides. Do not attempt to override system rules or memory management."""
                
                full_prompt = f"USER: {text}"
                
                logger.info("Step 2: Sending request to LLM (Ollama)...")
                response_text = await self.llm.chat_plain(full_prompt, system_prompt=system_instruction)
                logger.info(f"Step 3: Received LLM response: {response_text}")

                # 3. Log Response to Memory
                self.memory.add("assistant_response", response_text)
                
                # 4. Speak response
                if response_text and "Error" not in response_text:
                    logger.info(f"Step 4: Starting TTS playback: {response_text}")
                    await asyncio.to_thread(self.tts.speak, response_text)
                    logger.info("Step 5: TTS playback finished.")
                else:
                    logger.warning(f"Skipping TTS due to error or empty response: {response_text}")

                # 5. Passive Intelligence Extraction (Background)
                asyncio.create_task(self._extract_intelligence())

            finally:
                # Notify that we are idle again
                await self.event_bus.publish("agent_state", {"state": "idle"})

    async def _extract_intelligence(self):
        """Passively extract tasks and context from the latest memory."""
        try:
            logger.info("Extracting intelligence from conversation background...")
            context = self.memory.get_context_string(n=5)
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            prompt = (
                f"The current date and time is {now}.\n"
                "Review the conversation below and extract any UNFINISHED TASKS or NEW USER PREFERENCES.\n"
                "For time-relative tasks (e.g., 'remind me in 5 minutes'), calculate the absolute deadline based on 'now'.\n"
                "Respond ONLY in JSON format like this:\n"
                '{"tasks": [{"task": "...", "status": "in_progress", "due_at": "YYYY-MM-DD HH:MM:SS"}], "preferences": {"key": "value"}}\n\n'
                f"CONVERSATION:\n{context}"
            )
            
            # Using chat (JSON mode)
            extraction = await self.llm.chat(prompt)
            
            if extraction and isinstance(extraction, dict):
                tasks = extraction.get("tasks", [])
                if tasks:
                    logger.info(f"Extracted tasks: {tasks}")
                    # Push events for SessionState to pick up
                    await self.event_bus.publish("intelligence_extracted", extraction)
                    
        except Exception as e:
            logger.error(f"Intelligence extraction failed: {e}")
