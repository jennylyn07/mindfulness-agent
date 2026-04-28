"""
MindFlow — Grove (Habit Agent)
Returns a ChatCompletionAgent configured with the Grove system prompt.
"""
from semantic_kernel.agents import ChatCompletionAgent
from backend.kernel import build_kernel
from backend.prompts.habit import HABIT_PROMPT


def get_agent(memory_context: str = "") -> ChatCompletionAgent:
    instructions = HABIT_PROMPT.replace("{memoryContext}", memory_context)
    kernel = build_kernel()
    return ChatCompletionAgent(
        kernel=kernel,
        name="Grove",
        instructions=instructions,
    )
