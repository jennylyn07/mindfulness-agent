"""
MindFlow — Shared Semantic Kernel Instance
Creates one Kernel instance shared across all agents.
Import this module wherever an agent needs to be instantiated.

Microsoft Semantic Kernel SDK: semantic-kernel==1.41.3
Docs: https://learn.microsoft.com/semantic-kernel/overview/
"""
import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureTextEmbedding,
)
from dotenv import load_dotenv

# Resolve backend/.env relative to this file — CWD-independent
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=True)

_RAW_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
_KEY = os.getenv("AZURE_OPENAI_KEY", "")
_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
_EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")
_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

# Azure AI Foundry endpoints include /openai/v1 — strip to base domain only.
# AzureChatCompletion constructs the full path internally.
# e.g. https://resource.openai.azure.com/openai/v1 → https://resource.openai.azure.com/
from urllib.parse import urlparse as _urlparse
_parsed = _urlparse(_RAW_ENDPOINT)
_ENDPOINT = f"{_parsed.scheme}://{_parsed.netloc}/"


def build_kernel() -> Kernel:
    """
    Build and return a configured Semantic Kernel instance.
    Registers both the chat completion service and the embedding service.

    Called once per request — FastAPI is async so we build per-call
    rather than using a global to avoid thread-safety issues during streaming.
    """
    kernel = Kernel()

    kernel.add_service(
        AzureChatCompletion(
            service_id="azure_chat",
            deployment_name=_DEPLOYMENT,
            endpoint=_ENDPOINT,
            api_key=_KEY,
            api_version=_API_VERSION,
        )
    )

    kernel.add_service(
        AzureTextEmbedding(
            service_id="azure_embed",
            deployment_name=_EMBED_DEPLOYMENT,
            endpoint=_ENDPOINT,
            api_key=_KEY,
            api_version=_API_VERSION,
        )
    )

    return kernel


async def get_embedding(text: str) -> list[float]:
    """
    Generate a text embedding using text-embedding-3-small.
    Returns a 1536-dimension float vector.
    Smoke-tested in Hour 2 — must return len(vector) == 1536.
    """
    from openai import AsyncAzureOpenAI

    client = AsyncAzureOpenAI(
        api_key=_KEY,
        azure_endpoint=_ENDPOINT,
        api_version=_API_VERSION,
    )
    response = await client.embeddings.create(
        input=text,
        model=_EMBED_DEPLOYMENT,
    )
    return response.data[0].embedding
