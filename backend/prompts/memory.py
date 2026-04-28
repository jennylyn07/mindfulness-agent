"""Memory Agent system prompts — read and write pass."""

MEMORY_CONTEXT_TEMPLATE = """[MEMORY CONTEXT — assembled by Memory Agent, invisible to user]
User: {display_name}
Current mood: {current_mood}
Urgency: {urgency}
Time of day: {time_of_day}

Key facts about this user:
{facts_block}

Weekly summary: {week_summary}

Learned preferences:
- Preferred tone: {preferred_tone}
- Best journaling time: {best_journaling_time}
- Responds well to: {responds_well_to}
- Avoids: {avoids}

Recurring themes: {recurring_themes}
Breakthroughs: {breakthroughs}
[END MEMORY CONTEXT]"""

MEMORY_WRITE_PROMPT = """You are analyzing a mindfulness coaching conversation to extract
meaningful facts about the user that will help personalize future interactions.

Conversation:
User: {user_message}
Coach: {ai_response}

Extract any NEW facts revealed about the user — insights about their emotional patterns,
goals, challenges, preferences, or breakthroughs. Do NOT extract generic statements.
Only extract specific, personalized facts about THIS user.

For each fact, assign an importance score from 0.0 to 1.0:
- 0.9–1.0: Major breakthrough, core emotional pattern, significant life context
- 0.7–0.8: Useful preference or recurring theme
- 0.5–0.6: Minor detail, borderline useful
- Below 0.5: Too generic to store

Only include facts with importance >= 0.6.

Respond ONLY with valid JSON in this exact format:
{
  "facts": [
    {
      "content": "specific fact about the user",
      "source": "journal_entry",
      "importance": 0.85
    }
  ]
}

If no facts worth storing were revealed, respond with: {"facts": []}"""
