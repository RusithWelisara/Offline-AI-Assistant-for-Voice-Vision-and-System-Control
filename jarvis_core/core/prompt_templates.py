"""
Minimal Prompt Templates - Token-budgeted prompts for ultra-fast LLM responses.

Two modes only:
1. COMMAND MODE: JSON output, action execution
2. CHAT MODE: Plain text, conversational

Hard token budget: ≤140 tokens total per request
"""

from datetime import datetime


class PromptTemplate:
    """Ultra-minimal prompt templates with hard token budgets."""
    
    # Token budgets (approximate)
    MAX_SYSTEM_TOKENS = 40
    MAX_USER_TOKENS = 30
    MAX_CONTEXT_TOKENS = 40
    MAX_SCHEMA_TOKENS = 30
    TOTAL_BUDGET = 140
    
    @staticmethod
    def command_mode(user_text: str, context: str = None) -> tuple[str, str]:
        """
        COMMAND MODE - JSON output for action execution.
        
        Returns: (system_prompt, user_prompt)
        """
        # Ultra-short system instruction with action examples
        system = """You are a local command parser.
Return valid JSON only.

Schema:
{"speech":{"say":bool,"text":str},"actions":[{"type":str,"params":dict}]}

Actions:
- open_app: {"type":"open_app","params":{"app_name":"chrome"}}
- start_timer: {"type":"start_timer","params":{"duration_seconds":60}}

If no action: {"speech":{"say":false},"actions":[]}"""
        
        # Context injection (≤40 tokens, optional)
        context_str = ""
        if context:
            # Truncate context aggressively
            context_str = f"\nCONTEXT: {context[:100]}"
        
        # User prompt (≤30 tokens)
        user = f"{context_str}\nUSER: {user_text[:150]}\nJSON:"
        
        return system, user
    
    @staticmethod
    def chat_mode(user_text: str, context: str = None) -> tuple[str, str]:
        """
        CHAT MODE - Plain text conversational response.
        
        Returns: (system_prompt, user_prompt)
        """
        # Ultra-short system instruction (≤40 tokens)
        system = """You are JARVIS, a concise local assistant.
Keep answers under 2 sentences.
Be helpful and direct."""
        
        # Context injection (≤40 tokens, optional)
        context_str = ""
        if context:
            # Truncate context aggressively
            context_str = f"\nRECENT: {context[:80]}"
        
        # User prompt (≤30 tokens)
        user = f"{context_str}\nUSER: {user_text[:150]}"
        
        return system, user
    
    @staticmethod
    def get_minimal_context(memory_context: str, max_chars: int = 100) -> str:
        """
        Extracts minimal context from memory.
        
        Args:
            memory_context: Full context string from memory
            max_chars: Maximum characters to include
            
        Returns:
            Truncated context string
        """
        if not memory_context:
            return ""
        
        # Take only the most recent entries
        lines = memory_context.strip().split('\n')
        
        # Reverse to get most recent first
        recent_lines = lines[-3:] if len(lines) > 3 else lines
        
        # Join and truncate
        context = " | ".join(recent_lines)
        
        if len(context) > max_chars:
            context = context[:max_chars] + "..."
        
        return context
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters).
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    @staticmethod
    def validate_budget(system: str, user: str, max_tokens: int = TOTAL_BUDGET) -> bool:
        """
        Validates that prompts are within token budget.
        
        Args:
            system: System prompt
            user: User prompt
            max_tokens: Maximum allowed tokens
            
        Returns:
            True if within budget, False otherwise
        """
        total_tokens = PromptTemplate.estimate_tokens(system + user)
        return total_tokens <= max_tokens


# Pre-built templates for common scenarios
class QuickTemplates:
    """Pre-built minimal templates for ultra-fast access."""
    
    @staticmethod
    def greeting() -> str:
        """Fast greeting response."""
        return "Hello."
    
    @staticmethod
    def acknowledgment() -> str:
        """Fast acknowledgment."""
        return "Understood."
    
    @staticmethod
    def error() -> str:
        """Fast error response."""
        return "I encountered an error."
    
    @staticmethod
    def busy() -> str:
        """Fast busy response."""
        return "I'm currently processing another request."
