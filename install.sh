#!/bin/sh
# Z-Agent installer — one-liner:
#   curl -fsSL https://raw.githubusercontent.com/RydzzKen/Z-Agent/main/install.sh | bash
#
# Dilakukan script ini:
#   1. Clone (atau update) repo ke ~/.zagent
#   2. Buat Python venv & install dependency
#   3. Pasang launcher `zagent` ke ~/.local/bin
#
# Opsional env:
#   ZAGENT_HOME     — lokasi instalasi (default: ~/.zagent)
#   ZAGENT_BIN      — folder launcher (default: ~/.local/bin)
set -e

INSTALL_DIR="${ZAGENT_HOME:-$HOME/.zagent}"
BIN_DIR="${ZAGENT_BIN:-$HOME/.local/bin}"
REPO_URL="https://github.com/RydzzKen/Z-Agent.git"

say() { printf '\033[1;34m[Z-Agent]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[Z-Agent]\033[0m %s\n' "$*" >&2; exit 1; }

# --- 1. Git & Python ---
command -v git >/dev/null 2>&1 || die "git tidak ditemukan. Install dulu: sudo apt install git"
command -v python3 >/dev/null 2>&1 || die "python3 tidak ditemukan. Install dulu: sudo apt install python3 python3-venv"

# --- 2. Clone / update ---
if [ -d "$INSTALL_DIR/.git" ]; then
  say "Mengupdate Z-Agent di $INSTALL_DIR ..."
  git -C "$INSTALL_DIR" pull --ff-only || die "Update gagal. Cek koneksimu."
else
  say "Mengkloning Z-Agent ke $INSTALL_DIR ..."
  mkdir -p "$INSTALL_DIR"
  git clone --depth 1 "$REPO_URL" "$INSTALL_DIR" || die "Clone gagal. Cek koneksimu."
fi

cd "$INSTALL_DIR"

# --- 3. venv & dependency ---
say "Menyiapkan Python venv ..."
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate

say "Menginstall dependencies ..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

# --- 4. Launcher ---
mkdir -p "$BIN_DIR"
LAUNCHER="$BIN_DIR/zagent"
{
  printf '#!/bin/sh\n'
  printf 'exec "%s/.venv/bin/python" -m zagent "$@"\n' "$INSTALL_DIR"
} > "$LAUNCHER"
chmod +x "$LAUNCHER"

say "Selesai! Jalankan dengan: zagent"
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
  say "Tambahkan $BIN_DIR ke PATH dulu:"
  printf '  echo '"'"'export PATH="%s:$PATH"'"'"' >> ~/.bashrc && source ~/.bashrc\n' "$BIN_DIR"
fi