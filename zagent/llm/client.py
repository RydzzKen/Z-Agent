"""Provider API call layer (Gemini + OpenRouter)."""
import requests

from ..config import state
from . import schema
from . import usage


def _gemini_url():
    """Build Gemini endpoint URL, fallback jika BASE_URL belum diinisialisasi."""
    if state.BASE_URL:
        return state.BASE_URL
    key = state.GEMINI_API_KEY or state.PROVIDER.get("gemini_api_key", "")
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{state.MODEL_NAME}:generateContent?key={key}"
    )


def _call_gemini(contents, system_text, tools):
    if not (state.GEMINI_API_KEY or state.PROVIDER.get("gemini_api_key")):
        return None, "API key Gemini belum di-set. Gunakan /connect gemini <api_key>"
    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_text}]},
        "tools": tools,
    }
    # Thinking (Gemini 2.5+) -> minta thought part ikut dikembalikan.
    if state.THINK_ENABLED and state.MODEL_NAME.startswith("gemini-2.5"):
        payload["generationConfig"] = {"thinkingConfig": {"includeThoughts": True}}
    res = requests.post(_gemini_url(), json=payload, timeout=30)
    if res.status_code != 200:
        return None, f"Error {res.status_code}: {res.text}"
    data = res.json()
    usage.update_usage_stats(data)
    candidate = data.get("candidates", [{}])[0]
    return candidate.get("content", {}), None


def _call_openrouter(contents, system_text, tools):
    base = (state.PROVIDER.get("openrouter_base_url") or "https://openrouter.ai/api/v1").rstrip("/")
    url = base + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {state.PROVIDER['openrouter_api_key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/RydzzKen",
        "X-Title": "Z-Agent",
    }
    messages = [{"role": "system", "content": system_text}] + schema._gemini_contents_to_openai(contents)
    payload = {
        "model": state.MODEL_NAME,
        "messages": messages,
        "tools": schema._gemini_tools_to_openai(tools),
        "tool_choice": "auto",
    }
    # Minta reasoning ditampilkan bila model support (DeepSeek-R1, Qwen3, dll).
    if state.THINK_ENABLED:
        payload["include_reasoning"] = True
    res = requests.post(url, headers=headers, json=payload, timeout=30)
    if res.status_code != 200:
        return None, f"Error {res.status_code}: {res.text}"
    data = res.json()
    u = data.get("usage", {})
    usage.USAGE_STATS["requests"] += 1
    usage.USAGE_STATS["prompt_tokens"] += u.get("prompt_tokens", 0)
    usage.USAGE_STATS["candidates_tokens"] += u.get("completion_tokens", 0)
    usage.USAGE_STATS["total_tokens"] += u.get("total_tokens", 0)
    return schema._openai_response_to_gemini(data), None


def generate_response(contents, system_text, tools):
    """Kirim permintaan ke provider aktif. Return (model_content_format_gemini, error_str)."""
    if state.PROVIDER["name"] == "openrouter":
        return _call_openrouter(contents, system_text, tools)
    return _call_gemini(contents, system_text, tools)


def fetch_openrouter_models():
    base = (state.PROVIDER.get("openrouter_base_url") or "https://openrouter.ai/api/v1").rstrip("/")
    try:
        r = requests.get(base + "/models",
                         headers={"Authorization": f"Bearer {state.PROVIDER['openrouter_api_key']}"},
                         timeout=15)
        if r.status_code == 200:
            state.OR_MODELS = [m["id"] for m in r.json().get("data", [])]
    except Exception:
        pass
    return state.OR_MODELS


def chat_with_gemini(prompt):
    """Fungsi helper untuk chat langsung dengan Gemini (dipakai generate_docs)."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": "Kamu adalah asisten AI yang membantu membuat dokumentasi."}]}
    }
    res = requests.post(_gemini_url(), json=payload, timeout=30)
    if res.status_code == 200:
        data = res.json()
        return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Error: No response")
    return f"Error: {res.status_code}"
