"""
Intent Router - Fast-path system to avoid unnecessary LLM calls.

This router categorizes user input into:
- FAST_PATH: Zero LLM, instant responses
- COMMAND_PATH: LLM with JSON mode (action execution)
- CHAT_PATH: LLM with text mode (conversational)
- IGNORE: No processing needed
"""

import re
import logging

logger = logging.getLogger(__name__)

# Fast responses - zero LLM calls
FAST_RESPONSES = {
    "hi": "Hello.",
    "hello": "Hello.",
    "hey": "Hello.",
    "hey there": "Hello.",
    "hi there": "Hello.",
    "good morning": "Good morning.",
    "good afternoon": "Good afternoon.",
    "good evening": "Good evening.",
    "who are you": "I am JARVIS, your local assistant.",
    "what are you": "I am JARVIS, your local assistant.",
    "thanks": "You're welcome.",
    "thank you": "You're welcome.",
    "ok": "Understood.",
    "okay": "Understood.",
    "yes": "Understood.",
    "no": "Understood.",
}

# Command patterns - require LLM with JSON mode
COMMAND_PATTERNS = [
    r"^open\s+.+",
    r"^start\s+.+",
    r"^launch\s+.+",
    r"^run\s+.+",
    r"^close\s+.+",
    r"^stop\s+.+",
    r"^set\s+timer.+",
    r"^set\s+alarm.+",
    r"^remind\s+me.+",
    r"^turn\s+on\s+.+",
    r"^turn\s+off\s+.+",
    r"^play\s+.+",
    r"^pause\s+.+",
    r"^volume\s+.+",
    r"^search\s+for\s+.+",
    r"^find\s+.+",
    r"^create\s+.+",
    r"^delete\s+.+",
    r"^send\s+.+",
    r"^call\s+.+",
    r"^message\s+.+",
    r"^email\s+.+",
    r"^schedule\s+.+",
    r"^cancel\s+.+",
    r"^show\s+me\s+.+",
    r"^tell\s+me\s+about\s+.+",
    r"^what\s+is\s+.+",
    r"^what's\s+.+",
    r"^how\s+do\s+i\s+.+",
    r"^how\s+to\s+.+",
    r"^when\s+is\s+.+",
    r"^where\s+is\s+.+",
]

# Ignore patterns - filler words, noise
IGNORE_PATTERNS = [
    r"^um+$",
    r"^uh+$",
    r"^hmm+$",
    r"^ah+$",
    r"^er+$",
    r"^\s*$",  # Empty or whitespace only
]


class IntentRouter:
    """Routes user input to the appropriate processing path."""
    
    def __init__(self):
        self.fast_hit_count = 0
        self.command_count = 0
        self.chat_count = 0
        self.ignore_count = 0
    
    def route(self, text: str) -> tuple[str, str | None]:
        """
        Routes user input to the appropriate path.
        
        Args:
            text: User input text
            
        Returns:
            Tuple of (mode, response)
            - mode: "FAST_PATH", "COMMAND_PATH", "CHAT_PATH", or "IGNORE"
            - response: Pre-generated response for FAST_PATH, None otherwise
        """
        if not text or not isinstance(text, str):
            return "IGNORE", None
        
        t = text.lower().strip()
        
        # 1. Ignore path - filler words
        for pattern in IGNORE_PATTERNS:
            if re.match(pattern, t):
                self.ignore_count += 1
                logger.debug(f"Intent: IGNORE (pattern match)")
                return "IGNORE", None
        
        # 2. Fast path - instant responses
        if t in FAST_RESPONSES:
            self.fast_hit_count += 1
            response = FAST_RESPONSES[t]
            logger.info(f"Intent: FAST_PATH → '{response}' (saved LLM call)")
            return "FAST_PATH", response
        
        # 3. Command path - action execution
        for pattern in COMMAND_PATTERNS:
            if re.match(pattern, t):
                self.command_count += 1
                logger.info(f"Intent: COMMAND_PATH (pattern: {pattern})")
                return "COMMAND_PATH", None
        
        # 4. Chat path - conversational (default for short queries)
        # Limit to reasonable conversational length
        word_count = len(t.split())
        if word_count <= 20:
            self.chat_count += 1
            logger.info(f"Intent: CHAT_PATH ({word_count} words)")
            return "CHAT_PATH", None
        
        # 5. Fallback to command for longer queries
        self.command_count += 1
        logger.info(f"Intent: COMMAND_PATH (fallback, {word_count} words)")
        return "COMMAND_PATH", None
    
    def get_stats(self) -> dict:
        """Returns routing statistics."""
        total = self.fast_hit_count + self.command_count + self.chat_count + self.ignore_count
        return {
            "total_requests": total,
            "fast_path": self.fast_hit_count,
            "command_path": self.command_count,
            "chat_path": self.chat_count,
            "ignore": self.ignore_count,
            "llm_calls_saved": self.fast_hit_count + self.ignore_count,
            "llm_avoidance_rate": f"{(self.fast_hit_count + self.ignore_count) / total * 100:.1f}%" if total > 0 else "0%"
        }
    
    def log_stats(self):
        """Logs routing statistics."""
        stats = self.get_stats()
        logger.info(f"Intent Router Stats: {stats}")
