#!/bin/sh
# Z-Agent launcher for Termux / Android.
# - Dependency diambil dari pyproject.toml / requirements.txt.
# - Prioritas: uv (otomatis bikin venv & install). Kalau uv tidak ada,
#   fallback ke pip install -r requirements.txt.
# - /sdcard (FAT) tidak mendukung symlink, jadi venv uv dipindah ke /data.
# - ZAGENT_PLAIN sengaja TIDAK diset agar prompt_toolkit aktif
#   (popup autocomplete "/" saat mengetik).
#
# Usage:
#   ./run.sh          → TUI mode (default)
#   ./run.sh --cli    → CLI mode (text-based)
#   ZAGENT_CLI=1 ./run.sh  → CLI mode via env var
set -e

cd "$(dirname "$0")" || exit 1

# requirements.txt disiapkan otomatis kalau belum ada.
if [ ! -f requirements.txt ]; then
  printf "requests\nbeautifulsoup4\nprompt_toolkit\nyt-dlp\ntextual>=1.0\n" > requirements.txt
fi

if command -v uv >/dev/null 2>&1; then
  # Hanya gunakan path khusus Termux bila berjalan di Termux/Android.
  if [ -n "$PREFIX" ] && [ -d "$PREFIX" ] && [ -x /data ]; then
    export UV_PROJECT_ENVIRONMENT=/data/data/com.termux/files/home/agent2_venv
    export UV_LINK_MODE=copy
  fi
  exec uv run -m zagent "$@"
else
  echo "[run.sh] uv tidak ditemukan, pakai pip..."
  python -m pip install -r requirements.txt
  exec python -m zagent "$@"
fi
