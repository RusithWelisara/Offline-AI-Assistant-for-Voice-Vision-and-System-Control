import asyncio
import logging
import time
from datetime import datetime
from jarvis_core.core.planner import Planner
from jarvis_core.core.executor import Executor
from jarvis_core.core.memory import WorkingMemory
from jarvis_core.core.ltm import LongTermMemory
from jarvis_core.interfaces.voice import VoiceInterface

from jarvis_core.models.llm import LLM
from jarvis_core.speech.tts.piper_tts import PiperTTS
from jarvis_core.core.conversation import ConversationManager

from jarvis_core.core.decision_engine import DecisionEngine
from jarvis_core.core.state import SessionState

logger = logging.getLogger(__name__)

class AutonomyLoop:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.planner = Planner()
        self.executor = Executor(event_bus)
        self.memory = WorkingMemory()
        self.ltm = LongTermMemory() # Layer 3 Long Term Memory
        self.state = SessionState() # Layer 2 Session Memory
        self.voice = VoiceInterface(event_bus)
        
        self.llm = LLM()
        self.tts = PiperTTS()
        self.conversation_manager = ConversationManager(event_bus, self.llm, self.tts, self.memory, self.ltm)
        
        # Decision Engine
        self.decision_engine = DecisionEngine(self.memory, self.state)
        self.agent_state = "idle" # idle, busy
        self._subscribe()

    def _subscribe(self):
        self.event_bus.subscribe("agent_state", self.on_agent_state)
        self.event_bus.subscribe("intelligence_extracted", self.on_intelligence_extracted)

    async def on_agent_state(self, event):
        new_state = event.get("state")
        if new_state:
            logger.info(f"Agent state changed to: {new_state}")
            self.agent_state = new_state

    async def on_intelligence_extracted(self, event):
        tasks = event.get("tasks", [])
        prefs = event.get("preferences", {})
        
        if tasks:
            for task_data in tasks:
                self.state.add_active_task(task_data)
        
        if prefs:
            self.state.set_preferences(prefs)

    async def start(self):
        logger.info("Autonomy Loop started.")
        asyncio.create_task(self.event_bus.process_events())
        
        logger.info("Starting Voice Interface in background thread...")
        asyncio.create_task(asyncio.to_thread(self.voice.start))
        
        last_print_timestamp = 0
        
        while True:
            # 1. Update State Heartbeat
            self.state.update("last_active", time.time())
            
            # 2. Consult Decision Engine (Proper Decision Policy)
            current_time = time.time()
            decision = self.decision_engine.decide_action(self.agent_state, current_time)
            
            if decision:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                action_type = decision.get("type", "unknown")
                justification = decision.get("justification", "No justification provided")
                
                logger.info(f"Decision Engine triggered at {now_str}: {action_type}")
                logger.info(f"Justification: {justification}")
                
                # Execute the autonomous action
                if action_type == "FOLLOW_UP":
                    task_context = decision.get("context", {})
                    task_description = task_context.get("task", "Unknown task")
                    logger.info(f"Following up on task: {task_description}")
                    # TODO: Implement actual follow-up logic
                    # e.g., await self.conversation_manager.handle_task_followup(task_context)
                
                # Record the action with justification
                self.decision_engine.record_action(action_type, justification)
            
            # Debug: Print last 5 memory events ONLY if updated
            recent = self.memory.recent(5)
            if recent:
                newest_event = recent[-1]
                newest_timestamp = newest_event["timestamp"]
                
                if newest_timestamp > last_print_timestamp:
                    print("\n--- MEMORY DEBUG ---")
                    for event in recent:
                        print(f"[{event['type']}] {event['content']}")
                    print("--------------------\n")
                    last_print_timestamp = newest_timestamp
                    
                    # Heuristic: If we just had conversation, ensure we mark as idle eventually?
                    # Real state management should listen to events.

            await asyncio.sleep(5) # Check every 5 seconds
