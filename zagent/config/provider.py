"""Provider configuration & API key storage.

API key diambil dari environment variable / file .env / perintah /connect.
JANGAN di-hardcode. Provider yang didukung: gemini, openrouter.
"""
import os

from . import state
from ..ui import colors


def _load_env_file(path=".env"):
    """Muat variabel dari file .env ke os.environ (jika belum ada)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except FileNotFoundError:
        pass


_load_env_file()


def _read_dotenv():
    d = {}
    try:
        with open(state.ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return d


def _write_dotenv(d):
    try:
        with open(state.ENV_FILE, "w", encoding="utf-8") as f:
            for k, v in d.items():
                f.write(f'{k}="{v}"\n')
        return True
    except Exception:
        return False


def load_provider():
    """Muat konfigurasi provider. Prioritas: env -> .env -> legacy provider.json."""
    provider = {
        "name": os.environ.get("PROVIDER", "gemini").lower(),
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
        "openrouter_api_key": os.environ.get("OPENROUTER_API_KEY", ""),
        "openrouter_base_url": os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    }
    if provider["name"] not in ("gemini", "openrouter"):
        provider["name"] = "gemini"
    # fallback ke .env
    env = _read_dotenv()
    if not provider["gemini_api_key"] and env.get("GEMINI_API_KEY"):
        provider["gemini_api_key"] = env["GEMINI_API_KEY"]
    if not provider["openrouter_api_key"] and env.get("OPENROUTER_API_KEY"):
        provider["openrouter_api_key"] = env["OPENROUTER_API_KEY"]
    if not provider["openrouter_base_url"] and env.get("OPENROUTER_BASE_URL"):
        provider["openrouter_base_url"] = env["OPENROUTER_BASE_URL"]
    if not provider["name"] or provider["name"] == "gemini":
        if env.get("PROVIDER"):
            provider["name"] = env["PROVIDER"].lower()
    # legacy plaintext provider.json (hanya dibaca; akan dimigrasi saat /connect)
    if not provider["gemini_api_key"] or not provider["openrouter_api_key"]:
        try:
            with open(state.PROVIDER_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if not provider["gemini_api_key"] and saved.get("gemini_api_key"):
                    provider["gemini_api_key"] = saved["gemini_api_key"]
                if not provider["openrouter_api_key"] and saved.get("openrouter_api_key"):
                    provider["openrouter_api_key"] = saved["openrouter_api_key"]
                if not provider["openrouter_base_url"] and saved.get("openrouter_base_url"):
                    provider["openrouter_base_url"] = saved["openrouter_base_url"]
        except (FileNotFoundError, ValueError):
            pass
    return provider


import json  # noqa: E402  (digunakan oleh legacy provider.json)


# Muat konfigurasi provider (.env / env / legacy) saat modul diimpor,
# supaya API key yang tersimpan otomatis terbaca saat startup.
state.PROVIDER = load_provider()


def save_provider(provider):
    """Auto-save konfigurasi ke .env (gitignored). Hapus legacy provider.json."""
    env = _read_dotenv()
    env["PROVIDER"] = provider["name"]
    if provider.get("gemini_api_key"):
        env["GEMINI_API_KEY"] = provider["gemini_api_key"]
    if provider.get("openrouter_api_key"):
        env["OPENROUTER_API_KEY"] = provider["openrouter_api_key"]
    env["OPENROUTER_BASE_URL"] = provider.get("openrouter_base_url", "https://openrouter.ai/api/v1")
    ok = _write_dotenv(env)
    # migrasi: hapus legacy plaintext agar tidak ke-commit
    try:
        if os.path.exists(state.PROVIDER_FILE):
            os.remove(state.PROVIDER_FILE)
    except OSError:
        pass
    return ok


def active_key():
    """Kembalikan API key provider yang sedang aktif."""
    return state.PROVIDER["gemini_api_key"] if state.PROVIDER["name"] == "gemini" else state.PROVIDER["openrouter_api_key"]


def mask_api_key(key):
    """Tampilkan API key yang disensor agar tidak ter-expose di layar."""
    if not key:
        return "(belum di-set)"
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"


def ensure_initialized():
    """Inisialisasi GEMINI_API_KEY & BASE_URL dari key yang tersimpan (tanpa tulis ulang .env)."""
    from . import models as models_mod

    state.GEMINI_API_KEY = (
        "" if state.PROVIDER["name"] == "openrouter" else state.PROVIDER["gemini_api_key"]
    )
    if not state.BASE_URL:
        models_mod.set_model(state.MODEL_NAME)
    return True


def set_provider(name):
    """Ganti provider aktif menggunakan key yang SUDAH tersimpan (tanpa input ulang)."""
    from . import models

    name = name.lower()
    if name not in ("gemini", "openrouter"):
        return False
    state.PROVIDER["name"] = name
    if name == "openrouter":
        state.GEMINI_API_KEY = ""
        if state.MODEL_NAME.startswith("gemini"):
            models.set_model("openai/gpt-4o-mini")
    else:
        state.GEMINI_API_KEY = state.PROVIDER["gemini_api_key"]
        if "gemini" not in state.MODEL_NAME:
            models.set_model("gemini-flash-lite-latest")
        else:
            models.set_model(state.MODEL_NAME)
    save_provider(state.PROVIDER)
    return True


def set_key(name, key, base_url=""):
    """Simpan key untuk suatu provider & langsung aktifkan provider tersebut."""
    name = name.lower()
    if name == "openrouter":
        state.PROVIDER["openrouter_api_key"] = key
        if base_url:
            state.PROVIDER["openrouter_base_url"] = base_url
    else:
        state.PROVIDER["gemini_api_key"] = key
    set_provider(name)
    return True


def require_key():
    """Pastikan ada API key aktif; kalau belum, setup interaktif lalu simpan ke .env."""
    from ..tools import prompt

    if active_key():
        # Key sudah tersimpan -> inisialisasi GEMINI_API_KEY & BASE_URL.
        set_provider(state.PROVIDER["name"])
        return
    # Belum ada key -> setup interaktif pertama kali, lalu simpan ke .env
    import sys
    sys.stderr.write(
        f"ERROR: API key untuk provider '{state.PROVIDER['name']}' belum di-set.\n"
    )
    try:
        choice = prompt.get_input(
            f"{colors.C_BOLD}Provider (gemini/openrouter) [gemini] > {colors.C_RESET}"
        ).strip().lower() or "gemini"
        if choice not in ("gemini", "openrouter"):
            choice = "gemini"
        key = prompt.get_input(f"{colors.C_BOLD}Masukkan API key {choice} > {colors.C_RESET}").strip()
        if not key:
            sys.stderr.write("ERROR: API key kosong. Keluar.\n")
            sys.exit(1)
        base = "" if choice == "gemini" else "https://openrouter.ai/api/v1"
        set_key(choice, key, base)
        sys.stderr.write(
            f"{colors.C_GREEN}[+] Key '{choice}' disimpan ke .env. Menjalankan agent...{colors.C_RESET}\n"
        )
    except (EOFError, KeyboardInterrupt):
        sys.stderr.write(
            f"\nERROR: butuh API key. Jalankan {colors.C_BOLD}/connect <provider> <key>{colors.C_RESET} "
            f"atau set GEMINI_API_KEY di .env.\n"
        )
        sys.exit(1)
