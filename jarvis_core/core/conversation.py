import logging
import time
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
from jarvis_core.core.intent_router import IntentRouter
from jarvis_core.core.prompt_templates import PromptTemplate

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, event_bus: EventBus, llm: LLM, tts: PiperTTS, memory: WorkingMemory, ltm: LongTermMemory):
        self.event_bus = event_bus
        self.llm = llm
        self.tts = tts
        self.memory = memory
        self.ltm = ltm
        self.intent_router = IntentRouter()  # Fast-path routing
        self._subscribe()

    def _subscribe(self):
        self.event_bus.subscribe("user_speech", self.on_user_speech)

    async def on_user_speech(self, event):
        cycle_start = event.get("cycle_start_time")
        
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

                # 2. INTENT ROUTING - Fast-path system
                mode, fast_response = self.intent_router.route(text)
                
                # 3. Handle based on mode
                if mode == "FAST_PATH":
                    # Zero LLM - instant response
                    logger.info(f"⚡ FAST_PATH: '{fast_response}' (LLM call avoided)")
                    self.memory.add("assistant_response", fast_response)
                    await asyncio.to_thread(self.tts.speak, fast_response)
                    
                elif mode == "IGNORE":
                    # No processing needed
                    logger.info(f"⚡ IGNORE: Skipping processing for filler input")
                    
                elif mode == "COMMAND_PATH":
                    # LLM with JSON mode - action execution
                    logger.info(f"🔧 COMMAND_PATH: Using minimal JSON prompt")
                    await self._handle_command_mode(text)
                    
                elif mode == "CHAT_PATH":
                    # LLM with text mode - conversational
                    logger.info(f"💬 CHAT_PATH: Using minimal chat prompt")
                    await self._handle_chat_mode(text)
                
                # Log routing stats periodically
                if self.intent_router.get_stats()["total_requests"] % 10 == 0:
                    self.intent_router.log_stats()

            except Exception as e:
                logger.error(f"Error in on_user_speech: {e}")
            finally:
                if cycle_start:
                    total_delay = time.time() - cycle_start
                    logger.info(f"--- WHOLE CYCLE DELAY: {total_delay:.2f}s ---")
                
                # Notify that we are idle again
                await self.event_bus.publish("agent_state", {"state": "idle"})

    async def _handle_command_mode(self, text: str):
        """
        COMMAND MODE - Uses minimal JSON prompt for action execution.
        Token budget: ≤140 tokens
        """
        # Get minimal context (≤40 tokens)
        context_str = self.memory.get_context_string(n=3)  # Only last 3 entries
        minimal_context = PromptTemplate.get_minimal_context(context_str, max_chars=80)
        
        # Build minimal prompt
        system_prompt, user_prompt = PromptTemplate.command_mode(text, minimal_context)
        
        # Validate token budget
        if not PromptTemplate.validate_budget(system_prompt, user_prompt):
            logger.warning(f"Token budget exceeded! Estimated: {PromptTemplate.estimate_tokens(system_prompt + user_prompt)}")
        
        # Call LLM with JSON mode
        start_time = time.time()
        response_data = await self.llm.chat(user_prompt, system_prompt=system_prompt)
        llm_delay = time.time() - start_time
        
        logger.info(f"LLM Response (COMMAND): {llm_delay:.2f}s | Tokens: ~{PromptTemplate.estimate_tokens(system_prompt + user_prompt)}")
        
        if isinstance(response_data, dict):
            await self._process_response(response_data)
        else:
            logger.error(f"Invalid response format (not dict): {response_data}")
            await asyncio.to_thread(self.tts.speak, "I encountered an error processing the command.")
    
    async def _handle_chat_mode(self, text: str):
        """
        CHAT MODE - Uses minimal text prompt for conversational responses.
        Token budget: ≤140 tokens
        """
        # Get minimal context (≤40 tokens)
        context_str = self.memory.get_context_string(n=2)  # Only last 2 entries
        minimal_context = PromptTemplate.get_minimal_context(context_str, max_chars=60)
        
        # Build minimal prompt
        system_prompt, user_prompt = PromptTemplate.chat_mode(text, minimal_context)
        
        # Validate token budget
        if not PromptTemplate.validate_budget(system_prompt, user_prompt):
            logger.warning(f"Token budget exceeded! Estimated: {PromptTemplate.estimate_tokens(system_prompt + user_prompt)}")
        
        # Call LLM with plain text mode
        start_time = time.time()
        options = {
            "num_predict": 100,  # Max tokens
            "stop": ["User:", "USER:", "System:", "SYSTEM:"]
        }
        response_text = await self.llm.chat_plain(user_prompt, system_prompt=system_prompt, options=options)
        llm_delay = time.time() - start_time
        
        logger.info(f"LLM Response (CHAT): {llm_delay:.2f}s | Tokens: ~{PromptTemplate.estimate_tokens(system_prompt + user_prompt)}")
        
        if response_text and isinstance(response_text, str):
            # Log and speak the response
            self.memory.add("assistant_response", response_text)
            logger.info(f"Speaking: {response_text}")
            await asyncio.to_thread(self.tts.speak, response_text)
        else:
            logger.error(f"Invalid response: {response_text}")
            await asyncio.to_thread(self.tts.speak, "I'm not sure how to respond to that.")

    async def _process_response(self, data: dict):
        # 1. Speech
        speech = data.get("speech", {})
        text_to_speak = speech.get("text", "")
        
        # Speak if 'say' is True, OR if 'say' is missing but 'text' is present
        should_say = speech.get("say", "say" not in speech and bool(text_to_speak))
        
        if should_say and text_to_speak:
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
