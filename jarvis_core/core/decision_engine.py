import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    Decision Policy - Code logic, not vibes.
    The agent must answer ONE question repeatedly: "Should I act right now?"
    """
    def __init__(self, memory, session_state):
        self.memory = memory
        self.state = session_state
        self.default_cooldown = 3600  # 1 hour

    def decide_action(self, agent_state: str, now: float) -> Optional[Dict[str, Any]]:
        """
        Canonical Decision Function (Baseline)
        
        Decision Inputs:
        - Current agent state
        - Working memory (recent events)
        - Session memory (goals, unfinished tasks)
        - Time
        - Last autonomous action
        
        Returns:
        - None if no action should be taken
        - Dict with action details if action should be taken
        """
        # Rule 1: Never act if not idle
        if agent_state != "idle":
            logger.debug(f"Decision: No action - agent state is '{agent_state}', not 'idle'")
            return None

        # Rule 2: Respect autonomy cooldown
        last_action_time = self.state.get_last_autonomous_action_time()
        time_since_last_action = now - last_action_time
        
        if time_since_last_action < self.default_cooldown:
            remaining = self.default_cooldown - time_since_last_action
            logger.debug(f"Decision: No action - cooldown active ({remaining:.0f}s remaining)")
            return None

        # Rule 3: Check unfinished tasks
        unfinished_tasks = self.state.get_unfinished_tasks()
        if unfinished_tasks:
            # Get the oldest unfinished task
            oldest_task = min(unfinished_tasks, key=lambda t: t.get("added_at", 0))
            logger.info(f"Decision: FOLLOW_UP action - unfinished task: {oldest_task.get('task', 'unknown')}")
            return {
                "type": "FOLLOW_UP",
                "context": oldest_task,
                "justification": f"Unfinished task: {oldest_task.get('task', 'unknown')}"
            }

        # Rule 4: Otherwise, do nothing
        logger.debug("Decision: No action - no unfinished tasks and no other triggers")
        return None

    def should_act(self, agent_state: str, proposed_action_type: str = "generic_action") -> bool:
        """
        Legacy method for backward compatibility.
        Use decide_action() for new code.
        """
        decision = self.decide_action(agent_state, time.time())
        return decision is not None

    def record_action(self, action_type: str = "generic_action", justification: str = ""):
        """
        Record that an autonomous action occurred now.
        Logs the action with justification for debugging.
        """
        self.state.record_action(action_type)
        logger.info(f"Autonomous action recorded: {action_type} | Justification: {justification}")
