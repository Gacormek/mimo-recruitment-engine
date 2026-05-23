"""MiMo LLM integration client."""
import httpx
import logging
from ..config import MIMO_API_URL, MIMO_MODEL, MIMO_API_KEY

logger = logging.getLogger("mimo.client")

_client: httpx.AsyncClient = None


async def get_client() -> httpx.AsyncClient:
    """Get or create the async HTTP client."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=120.0)
    return _client


async def mimo_chat(
    system: str = "You are a helpful AI assistant.",
    user: str = "",
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Send a chat completion request to the MiMo LLM endpoint.
    
    Args:
        system: System prompt
        user: User message
        temperature: Sampling temperature
        max_tokens: Maximum response tokens
    
    Returns:
        The assistant's response text
    """
    client = await get_client()
    
    payload = {
        "model": MIMO_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {MIMO_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = await client.post(
            f"{MIMO_API_URL}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content.strip()
    except httpx.HTTPStatusError as e:
        logger.error(f"MiMo API HTTP error: {e.response.status_code} — {e.response.text}")
        raise RuntimeError(f"MiMo API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"MiMo API call failed: {e}")
        raise


async def close_client():
    """Close the HTTP client."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
