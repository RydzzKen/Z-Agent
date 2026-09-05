"""Shared mutable state & path configuration for Z-Agent.

All cross-module globals live here so modules can mutate them via
`state.X = ...` instead of relying on per-module ``global`` declarations
(which get messy once code is split across packages.
"""
import os

# ========== PATHS ==========
ROOT_DIR = os.path.abspath(".")
# Semua operasi file agent DIBATASI ke folder workspace/ ini saja.
WORKSPACE_DIR = os.path.join(ROOT_DIR, "workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)
# File konfigurasi & rahasia tetap di root project (sudah di-.gitignore).
PROVIDER_FILE = os.path.join(ROOT_DIR, "provider.json")  # legacy plaintext (dimigrasi lalu dihapus)
ENV_FILE = os.path.join(ROOT_DIR, ".env")
MEMORY_FILE = os.path.join(WORKSPACE_DIR, "memory.json")
TASK_FILE = os.path.join(WORKSPACE_DIR, "tasks.json")
PROJECT_CONFIG_FILE = os.path.join(WORKSPACE_DIR, "project.json")
SESSION_FILE = os.path.join(WORKSPACE_DIR, "sessions.json")

# ========== RUNTIME MUTABLE STATE ==========
PROVIDER = {
    "name": "gemini",
    "gemini_api_key": "",
    "openrouter_api_key": "",
    "openrouter_base_url": "https://openrouter.ai/api/v1",
}
GEMINI_API_KEY = ""
MODEL_NAME = "gemini-flash-lite-latest"
BASE_URL = ""
THINK_ENABLED = False
LAST_MODEL_LIST = []  # daftar yang sedang ditampilkan, agar /model <nomor> konsisten
OR_MODELS = []

# ========== USAGE TRACKING ==========
# Menghitung total token yang dipakai selama sesi (dari usageMetadata Gemini).
USAGE_STATS = {
    "requests": 0,
    "prompt_tokens": 0,
    "candidates_tokens": 0,
    "total_tokens": 0,
}
