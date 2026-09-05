"""Token usage tracking (accumulated across the session)."""
from ..config import state

USAGE_STATS = state.USAGE_STATS


def update_usage_stats(response_data):
    """Ambil usageMetadata dari response Gemini dan akumulasi ke USAGE_STATS."""
    meta = response_data.get("usageMetadata")
    if not meta:
        return
    USAGE_STATS["requests"] += 1
    USAGE_STATS["prompt_tokens"] += meta.get("promptTokenCount", 0) or 0
    USAGE_STATS["candidates_tokens"] += meta.get("candidatesTokenCount", 0) or 0
    USAGE_STATS["total_tokens"] += meta.get("totalTokenCount", 0) or 0
