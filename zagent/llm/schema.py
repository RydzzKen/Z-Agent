"""Schema & message-format conversion between Gemini and OpenAI/OpenRouter.

Internal `contents` tetap pakai format Gemini. Konversi ke/dekat format
OpenAI hanya dilakukan di batas pemanggilan (untuk OpenRouter).
"""
from ..config import state

_SCHEMA_TYPE_MAP = {
    "STRING": "string", "NUMBER": "number", "INTEGER": "integer",
    "BOOLEAN": "boolean", "OBJECT": "object", "ARRAY": "array",
}


def _normalize_schema(node):
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k == "type" and isinstance(v, str):
            out[k] = _SCHEMA_TYPE_MAP.get(v, v.lower())
        elif k == "properties" and isinstance(v, dict):
            out[k] = {pk: _normalize_schema(pv) for pk, pv in v.items()}
        elif k == "items" and isinstance(v, dict):
            out[k] = _normalize_schema(v)
        else:
            out[k] = v
    return out


def _gemini_tools_to_openai(tools):
    openai_tools = []
    for grp in tools:
        for decl in grp.get("functionDeclarations", []):
            params = decl.get("parameters") or {"type": "OBJECT", "properties": {}}
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": decl["name"],
                    "description": decl.get("description", ""),
                    "parameters": _normalize_schema(params),
                },
            })
    return openai_tools


def _gemini_contents_to_openai(contents):
    messages = []
    pending_ids = []
    for item in contents:
        role = item.get("role")
        parts = item.get("parts", [])
        if role == "user":
            texts = [p["text"] for p in parts if "text" in p]
            frs = [p["functionResponse"] for p in parts if "functionResponse" in p]
            for fr in frs:
                name = fr["name"]
                out = str(fr.get("response", {}).get("output", ""))
                tid = None
                for e in pending_ids:
                    if e["name"] == name:
                        tid = e["id"]
                        break
                messages.append({"role": "tool", "tool_call_id": tid or ("call_" + name), "content": out})
            if texts:
                messages.append({"role": "user", "content": "\n".join(texts)})
        elif role == "model":
            texts = [p["text"] for p in parts if "text" in p]
            fcs = [p["functionCall"] for p in parts if "functionCall" in p]
            msg = {"role": "assistant", "content": "\n".join(texts) if texts else None}
            if fcs:
                tool_calls = []
                pending_ids = []
                for fc in fcs:
                    cid = "call_" + fc["name"]
                    pending_ids.append({"name": fc["name"], "id": cid})
                    tool_calls.append({
                        "id": cid, "type": "function",
                        "function": {
                            "name": fc["name"],
                            "arguments": json.dumps(fc.get("args", {}), ensure_ascii=False),
                        },
                    })
                msg["tool_calls"] = tool_calls
            messages.append(msg)
    return messages


def _openai_response_to_gemini(data):
    msg = data["choices"][0]["message"]
    parts = []
    # Tangkap reasoning/thinking dari model OpenRouter yang support (R1, Qwen3, dll).
    reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
    if reasoning and state.THINK_ENABLED:
        parts.append({"thought": True, "text": reasoning})
    if msg.get("content"):
        parts.append({"text": msg["content"]})
    for tc in msg.get("tool_calls", []) or []:
        fn = tc["function"]
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except Exception:
            args = {}
        parts.append({"functionCall": {"name": fn["name"], "args": args}})
    return {"role": "model", "parts": parts}


import json  # noqa: E402
