"""Model selection & BASE_URL construction."""
from . import state


# Daftar model Gemini yang tersedia untuk dipilih via perintah /model
AVAILABLE_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]


def set_model(model_name):
    """Ubah model yang digunakan secara runtime (update MODEL_NAME & BASE_URL)."""
    state.MODEL_NAME = model_name
    state.BASE_URL = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={state.GEMINI_API_KEY}"
    )
