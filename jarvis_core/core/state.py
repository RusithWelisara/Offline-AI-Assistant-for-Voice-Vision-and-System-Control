import json
import os
import time
import logging

logger = logging.getLogger(__name__)

class SessionState:
    def __init__(self, state_file="jarvis_state.json"):
        self.state_file = state_file
        self.state = {
            "session_id": str(int(time.time())),
            "last_active": time.time(),
            "agent_state": "idle",
            "active_tasks": [],
            "preferences": {},
            "action_history": {},  # Key: action_type, Value: timestamp
            "last_autonomous_action": 0  # Timestamp of last autonomous action
        }
        self.load()

    def load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Merge loaded data with defaults (preserving new session_id if desired, 
                    # but usually session state persists context, so lets load it all)
                    self.state.update(data)
                    logger.info("Session State loaded.")
            except Exception as e:
                logger.error(f"Failed to load session state: {e}")

    def save(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")

    def update(self, key, value):
        self.state[key] = value
        self.save()

    def get(self, key, default=None):
        return self.state.get(key, default)

    def record_action(self, action_type):
        """Record that an autonomous action occurred now."""
        timestamp = time.time()
        
        # Update history
        history = self.state.get("action_history", {})
        history[action_type] = timestamp
        self.state["action_history"] = history
        
        # Update last active overall
        self.state["last_autonomous_action"] = timestamp
        
        self.save()

    def check_cooldown(self, action_type, cooldown_seconds=3600):
        """
        Check if specific action is on cooldown.
        Returns True if ON COOLDOWN (do not act).
        Returns False if SAFE TO ACT.
        """
        history = self.state.get("action_history", {})
        last_time = history.get(action_type, 0)
        
        if (time.time() - last_time) < cooldown_seconds:
            return True # On cooldown
        return False

    def add_active_task(self, task_data):
        """Add an extracted task to active_tasks list."""
        tasks = self.state.get("active_tasks", [])
        # Simple deduplication by task name
        if not any(t['task'] == task_data['task'] for t in tasks):
            task_data["added_at"] = time.time()
            tasks.append(task_data)
            self.state["active_tasks"] = tasks
            self.save()
            logger.info(f"Task added to session state: {task_data['task']}")

    def set_preferences(self, prefs):
        """Merge new preferences into existing ones."""
        existing = self.state.get("preferences", {})
        existing.update(prefs)
        self.state["preferences"] = existing
        self.save()
        logger.info(f"Preferences updated: {prefs}")

    def get_unfinished_tasks(self):
        """Get all unfinished tasks (not completed)."""
        tasks = self.state.get("active_tasks", [])
        unfinished = [
            task for task in tasks 
            if task.get("status") not in ["completed", "done", "finished"]
        ]
        return unfinished

    def get_last_autonomous_action_time(self):
        """Get timestamp of last autonomous action."""
        return self.state.get("last_autonomous_action", 0)

    def clear(self):
        """Reset state to defaults and save."""
        self.state = {
            "session_id": str(int(time.time())),
            "last_active": time.time(),
            "agent_state": "idle",
            "active_tasks": [],
            "preferences": {},
            "action_history": {},
            "last_autonomous_action": 0
        }
        self.save()
        logger.info(f"Session state cleared: {self.state_file}")