from jarvis_core.models.llm import LLM

class Planner:
    def __init__(self):
        self.llm = LLM()

    async def plan(self, context):
        # Use LLM to generate a plan based on context
        response = await self.llm.generate(f"Plan for: {context}")
        return response
