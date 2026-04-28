"""
MindFlow — Sage (Mindfulness Agent)
Returns a ChatCompletionAgent configured with the Sage system prompt.
Memory context is injected into the instructions before the agent is built.
"""
from semantic_kernel.agents import ChatCompletionAgent
from backend.kernel import build_kernel
from backend.prompts.mindfulness import MINDFULNESS_PROMPT


def get_agent(memory_context: str = "") -> ChatCompletionAgent:
    """
    Build and return a Sage ChatCompletionAgent with memory context injected.
    Called once per request from the chat route.
    """
    instructions = MINDFULNESS_PROMPT.replace("{memoryContext}", memory_context)
    kernel = build_kernel()
    return ChatCompletionAgent(
        kernel=kernel,
        name="Sage",
        instructions=instructions,
    )
