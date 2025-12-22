import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class LongTermMemory:
    """
    Manages Long-Term Memory (Layer 3) stored in JSON files.
    Enforces strict separation of Profile, Preferences, and Habits.
    """
    def __init__(self, ltm_dir: str = "jarvis_core/LTM"):
        self.ltm_dir = Path(ltm_dir)
        self.profile_path = self.ltm_dir / "profile.json"
        self.preferences_path = self.ltm_dir / "preferences.json"
        self.habits_path = self.ltm_dir / "habits.json"
        
        self.profile = self._load_json(self.profile_path)
        self.preferences = self._load_json(self.preferences_path)
        self.habits = self._load_json(self.habits_path)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load LTM file {path}: {e}")
            return {}

    def _save_json(self, path: Path, data: Dict[str, Any]):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save LTM file {path}: {e}")

    def get_profile_string(self) -> str:
        """Returns formatted string for System Prompt (Layer 3)."""
        interests = ", ".join(self.profile.get("core_interests", []))
        return (
            f"PERSONAL PROFILE (LTM):\n"
            f"- Name: {self.profile.get('user_name', 'Unknown')}\n"
            f"- Location: {self.profile.get('location', 'Unknown')}\n"
            f"- Role: {self.profile.get('student', False) and 'Student' or 'User'}\n"
            f"- Interests: {interests}\n"
            f"- Trust Level: {self.profile.get('assistant_trust_level', 'limited')}"
        )

    def get_preferences_string(self) -> str:
        """Returns formatted string for System Prompt."""
        prefs = "\n".join([f"- {k}: {v}" for k, v in self.preferences.items()])
        return f"USER PREFERENCES (LTM):\n{prefs}"

    def get_habits_string(self) -> str:
        """Returns formatted string for System Prompt."""
        # Summarize habits for context
        habits_str = []
        for category, details in self.habits.items():
            habits_str.append(f"- {category}: {json.dumps(details)}")
        return "USER HABITS (LTM):\n" + "\n".join(habits_str)

    def process_proposal(self, proposal: Dict[str, Any]) -> bool:
        """
        Evaluates and applies a memory proposal.
        Returns True if accepted/applied, False otherwise.
        
        Proposal Schema:
        {
            "type": "preference" | "habit" | "profile",
            "key": "string",
            "value": any,
            "confidence": float,
            "reason": "string"
        }
        """
        p_type = proposal.get("type")
        key = proposal.get("key")
        value = proposal.get("value")
        confidence = proposal.get("confidence", 0.0)
        reason = proposal.get("reason")

        logger.info(f"LTM Proposal Received: {proposal}")

        # Basic Policy:
        # 1. Profile updates require extremely high confidence or manual confirmation (skipped for auto-update usually).
        # 2. Preferences require high confidence (> 0.7).
        # 3. Habits require high confidence (> 0.8) usually derived from stats, but if LLM proposes, we treat cautiously.

        if p_type == "profile":
            # Profile is rarely changed by LLM. Reject for safety unless very specific logic exists.
            logger.warning("Rejected PROFILE update proposal from LLM (Safety Policy).")
            return False

        elif p_type == "preference":
            if confidence >= 0.7:
                self.preferences[key] = value
                self._save_json(self.preferences_path, self.preferences)
                logger.info(f"ACCEPTED Preference Update: {key} = {value}")
                return True
            else:
                logger.info(f"REJECTED Preference Update: Confidence {confidence} < 0.7")
                return False

        elif p_type == "habit":
            # Habits should ideally be updated by statistical analysis, not just one-shot LLM.
            # But if we allow it:
            if confidence >= 0.8:
                # Merge logic might be needed for nested habits, but simple overwrite for now if key exists at top level
                # Or if key is like "study_sessions.preferred_duration_minutes"
                
                # Simple implementation: Top level keys only for now or overwrite
                self.habits[key] = value
                self._save_json(self.habits_path, self.habits)
                logger.info(f"ACCEPTED Habit Update: {key} = {value}")
                return True
            else:
                logger.info(f"REJECTED Habit Update: Confidence {confidence} < 0.8")
                return False

        return False
