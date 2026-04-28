"""
MindFlow — River (Journal Agent)
Returns a ChatCompletionAgent configured with the River system prompt.
River appends a [SAVE_ENTRY]...[/SAVE_ENTRY] block at the END of every
response — parsed and stripped by the chat route's buffer parser.

Decision 1 (locked): SAVE_ENTRY block always at absolute end via prompt
directive. No TransformStream state machine needed.
"""
from semantic_kernel.agents import ChatCompletionAgent
from backend.kernel import build_kernel
from backend.prompts.journal import JOURNAL_PROMPT


def get_agent(memory_context: str = "") -> ChatCompletionAgent:
    """
    Build and return a River ChatCompletionAgent with memory context injected.
    Called once per request from the chat route.
    """
    instructions = JOURNAL_PROMPT.replace("{memoryContext}", memory_context)
    kernel = build_kernel()
    return ChatCompletionAgent(
        kernel=kernel,
        name="River",
        instructions=instructions,
    )
