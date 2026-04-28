"""
MindFlow — Lumen (Insights Agent)
Returns a ChatCompletionAgent configured with journal RAG context + memory context.

Flow:
  1. Fetch recent mood logs from Cosmos (for sparkline + context)
  2. Run hybrid search over journal entries in AI Search
  3. Build Lumen's instructions with both {journalContext} and {memoryContext} injected
  4. Return agent — caller streams response
"""
from semantic_kernel.agents import ChatCompletionAgent
from backend.kernel import build_kernel
from backend.prompts.insights import INSIGHTS_PROMPT
from backend.providers import search_provider


async def get_agent(user_id: str, user_query: str, memory_context: str = "") -> ChatCompletionAgent:
    """
    Build Lumen with journal context from RAG + memory context.
    Async because search_provider.search() is async.
    """
    journal_context = await search_provider.search(
        query=user_query,
        user_id=user_id,
        top_k=5,
    )

    instructions = (
        INSIGHTS_PROMPT
        .replace("{journalContext}", journal_context or "No journal entries indexed yet.")
        .replace("{memoryContext}", memory_context)
    )

    kernel = build_kernel()
    return ChatCompletionAgent(
        kernel=kernel,
        name="Lumen",
        instructions=instructions,
    )
