"""
Test script for the token-budgeted prompt system.

Tests:
1. Intent routing (FAST_PATH, COMMAND_PATH, CHAT_PATH, IGNORE)
2. Prompt template generation
3. Token budget validation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis_core.core.intent_router import IntentRouter
from jarvis_core.core.prompt_templates import PromptTemplate


def test_intent_router():
    """Test intent routing logic."""
    print("=" * 60)
    print("TESTING INTENT ROUTER")
    print("=" * 60)
    
    router = IntentRouter()
    
    test_cases = [
        # (input, expected_mode)
        ("hi", "FAST_PATH"),
        ("hello", "FAST_PATH"),
        ("thanks", "FAST_PATH"),
        ("who are you", "FAST_PATH"),
        ("um", "IGNORE"),
        ("", "IGNORE"),
        ("open chrome", "COMMAND_PATH"),
        ("set timer for 5 minutes", "COMMAND_PATH"),
        ("turn on the lights", "COMMAND_PATH"),
        ("how are you", "CHAT_PATH"),
        ("what's the weather", "CHAT_PATH"),
        ("tell me a joke", "COMMAND_PATH"),  # Matches pattern
    ]
    
    passed = 0
    failed = 0
    
    for user_input, expected_mode in test_cases:
        mode, response = router.route(user_input)
        
        if mode == expected_mode:
            print(f"[PASS] '{user_input}' -> {mode} (response: {response})")
            passed += 1
        else:
            print(f"[FAIL] '{user_input}' -> {mode} (expected: {expected_mode})")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    print(f"\nRouter Stats: {router.get_stats()}")
    print()


def test_prompt_templates():
    """Test prompt template generation and token budgets."""
    print("=" * 60)
    print("TESTING PROMPT TEMPLATES")
    print("=" * 60)
    
    # Test COMMAND mode
    print("\n--- COMMAND MODE ---")
    system, user = PromptTemplate.command_mode("open chrome", context="User opened firefox")
    
    print(f"System Prompt ({PromptTemplate.estimate_tokens(system)} tokens):")
    print(system)
    print(f"\nUser Prompt ({PromptTemplate.estimate_tokens(user)} tokens):")
    print(user)
    
    total_tokens = PromptTemplate.estimate_tokens(system + user)
    within_budget = PromptTemplate.validate_budget(system, user)
    
    print(f"\nTotal Tokens: ~{total_tokens}")
    print(f"Within Budget (<={PromptTemplate.TOTAL_BUDGET}): {'[YES]' if within_budget else '[NO]'}")
    
    # Test CHAT mode
    print("\n--- CHAT MODE ---")
    system, user = PromptTemplate.chat_mode("how are you", context="User said hello")
    
    print(f"System Prompt ({PromptTemplate.estimate_tokens(system)} tokens):")
    print(system)
    print(f"\nUser Prompt ({PromptTemplate.estimate_tokens(user)} tokens):")
    print(user)
    
    total_tokens = PromptTemplate.estimate_tokens(system + user)
    within_budget = PromptTemplate.validate_budget(system, user)
    
    print(f"\nTotal Tokens: ~{total_tokens}")
    print(f"Within Budget (<={PromptTemplate.TOTAL_BUDGET}): {'[YES]' if within_budget else '[NO]'}")
    
    # Test context truncation
    print("\n--- CONTEXT TRUNCATION ---")
    long_context = "User opened chrome. User searched for weather. User closed chrome. User opened firefox. User searched for news."
    minimal = PromptTemplate.get_minimal_context(long_context, max_chars=50)
    
    print(f"Original ({len(long_context)} chars): {long_context}")
    print(f"Minimal ({len(minimal)} chars): {minimal}")
    print()


def test_token_estimation():
    """Test token estimation accuracy."""
    print("=" * 60)
    print("TESTING TOKEN ESTIMATION")
    print("=" * 60)
    
    test_strings = [
        "Hello",
        "This is a test",
        "The quick brown fox jumps over the lazy dog",
        "A" * 100,
    ]
    
    for s in test_strings:
        estimated = PromptTemplate.estimate_tokens(s)
        print(f"'{s[:50]}...' -> ~{estimated} tokens (chars: {len(s)})")
    
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TOKEN-BUDGETED PROMPT SYSTEM - TEST SUITE")
    print("=" * 60 + "\n")
    
    test_intent_router()
    test_prompt_templates()
    test_token_estimation()
    
    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
