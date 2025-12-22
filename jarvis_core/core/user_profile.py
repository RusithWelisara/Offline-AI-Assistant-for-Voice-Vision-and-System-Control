"""
Personal Profile (User) - Facts only. No psychology.
This is not memory. This is contextual identity.
Never rewritten by the LLM. Never "inferred" beyond facts.
"""

USER_PROFILE = {
    "user_name": "Rusith",
    "age": 16,
    "location": "Sri Lanka",
    "primary_interests": ["AI", "robotics", "aerospace"],
    "current_focus": "building an offline autonomous assistant",
    "preferred_interaction_style": "direct, minimal, non-annoying",
    "assistant_role": "offline autonomous system assistant"
}

def get_user_profile_string():
    """Convert user profile to system prompt format."""
    interests = ", ".join(USER_PROFILE['primary_interests'])
    return f"""PERSONAL PROFILE:
- Name: {USER_PROFILE['user_name']}
- Age: {USER_PROFILE['age']}
- Location: {USER_PROFILE['location']}
- Primary Interests: {interests}
- Current Focus: {USER_PROFILE['current_focus']}
- Preferred Interaction Style: {USER_PROFILE['preferred_interaction_style']}
- Assistant Role: {USER_PROFILE['assistant_role']}"""

