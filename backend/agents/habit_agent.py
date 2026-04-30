"""
MindFlow — Grove (Habit Agent)
Returns a ChatCompletionAgent configured with the Grove system prompt
and live habit data from Cosmos DB.
"""
from semantic_kernel.agents import ChatCompletionAgent
from backend.kernel import build_kernel
from backend.prompts.habit import HABIT_PROMPT


def get_agent(
    memory_context: str = "",
    habit_list: str = "No active habits yet.",
    today_logs: str = "None completed yet today.",
    streaks: str = "",
) -> ChatCompletionAgent:
    instructions = (
        HABIT_PROMPT
        .replace("{memoryContext}", memory_context)
        .replace("{habitList}", habit_list)
        .replace("{todayLogs}", today_logs)
        .replace("{streaks}", streaks or "No active habits yet.")
    )
    kernel = build_kernel()
    return ChatCompletionAgent(
        kernel=kernel,
        name="Grove",
        instructions=instructions,
    )
