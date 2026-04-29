"""
MindFlow — Orchestrator Agent
Classifies every incoming message before routing to a specialist.
JSON mode, temperature=0, no streaming. Target latency: <300ms.
Falls back to "journal" when intent is unclear.
"""
import json
import os
from backend.models.schemas import OrchestratorResult
from backend.prompts.orchestrator import ORCHESTRATOR_PROMPT

_FALLBACK = OrchestratorResult(
    agent="journal", confidence=0.5, mood="unknown", urgency="low"
)


async def classify(message: str) -> OrchestratorResult:
    """
    One JSON-mode LLM call to classify the user's intent.
    Returns OrchestratorResult. Never raises — returns fallback on any error.
    """
    try:
        from openai import AsyncAzureOpenAI
        from urllib.parse import urlparse as _up

        _raw = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        _p = _up(_raw)
        _base_ep = f"{_p.scheme}://{_p.netloc}/"

        client = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY", ""),
            azure_endpoint=_base_ep,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        )

        response = await client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            messages=[
                {"role": "system", "content": ORCHESTRATOR_PROMPT},
                {"role": "user", "content": message},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=128,
        )

        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)

        return OrchestratorResult(
            agent=data.get("agent", "journal"),
            confidence=float(data.get("confidence", 0.5)),
            mood=data.get("mood", "unknown"),
            urgency=data.get("urgency", "low"),
        )

    except Exception as e:
        print(f"[Orchestrator] classify() failed: {e} — using fallback")
        return _FALLBACK
