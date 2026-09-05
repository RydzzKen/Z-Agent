"""Long-term memory storage (memory.json) & remember/get tool implementations."""
import json

from ..config import state
from ..ui import colors


def load_memory_data():
    if not os.path.exists(state.MEMORY_FILE):
        return {}
    try:
        with open(state.MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_memory_data(data):
    try:
        with open(state.MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"{colors.C_RED}[-] Gagal menyimpan memori: {e}{colors.C_RESET}")
        return False


def remember_fact(key, value):
    mem_data = load_memory_data()
    mem_data[key] = value
    if save_memory_data(mem_data):
        return f"Berhasil mengingat: '{key}' = '{value}'"
    return "Gagal menyimpan fakta ke memori."


def get_memory():
    data = load_memory_data()
    if not data:
        return "Memori masih kosong."
    return f"--- ISI MEMORI TERSEDIA ---\n{json.dumps(data, indent=2, ensure_ascii=False)}"


import os  # noqa: E402
