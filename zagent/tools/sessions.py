"""Session storage: simpan/muat riwayat percakapan (contents) ke disk.

Konsep:
- Seluruh sesi disimpan dalam satu file `sessions.json`.
- Bentuk file:
  {
    "active": "20260902-143000",
    "sessions": {
      "<session_id>": {"created": "...", "updated": "...", "contents": [...]}
    }
  }
- `contents` ditulis ulang setiap kali berubah agar tidak hilang saat app ditutup.
"""
import json
import uuid
from datetime import datetime

from ..config import state
from ..ui import colors
from ..ui import format as fmt


def _load_all():
    if not __import__("os").path.exists(state.SESSION_FILE):
        return {"active": None, "sessions": {}}
    try:
        with open(state.SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"active": None, "sessions": {}}


def _save_all(data):
    try:
        with open(state.SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def new_session_id():
    return datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{uuid.uuid4().hex[:4]}"


def save_session(session_id, contents):
    """Simpan (tulis ulang) riwayat sebuah sesi."""
    data = _load_all()
    sessions = data.setdefault("sessions", {})
    if session_id not in sessions:
        sessions[session_id] = {"created": datetime.now().isoformat()}
    sessions[session_id]["updated"] = datetime.now().isoformat()
    sessions[session_id]["contents"] = contents
    name = _first_user_text(contents)
    if name:
        sessions[session_id]["name"] = name
    data["active"] = session_id
    return _save_all(data)


def _first_user_text(contents):
    """Ambil teks pesan user pertama (untuk nama sesi)."""
    for item in contents:
        if item.get("role") == "user":
            for p in item.get("parts", []):
                if "text" in p and p["text"]:
                    text = " ".join(p["text"].split())
                    if text:
                        return text
    return ""


def session_name(meta):
    """Nama tampilan sesi — dari pesan pertama / nama tersimpan."""
    if not meta:
        return ""
    name = meta.get("name") or ""
    if name:
        return name
    return _first_user_text(meta.get("contents", []))


def get_meta(session_id):
    """Ambil metadata satu sesi; None jika tidak ada."""
    return _load_all().get("sessions", {}).get(session_id)


def get_active_session():
    return _load_all().get("active")


def begin_new_session():
    """Mulai sesi baru: hapus penanda 'active' tanpa menulis sesi kosong.

    Sesi sungguhan baru dibuat otomatis saat pesan pertama dikirim.
    """
    data = _load_all()
    data["active"] = None
    return _save_all(data)


def list_sessions():
    """Kembalikan daftar sesi terurut (terbaru dulu)."""
    data = _load_all()
    sessions = data.get("sessions", {})
    ordered = sorted(
        sessions.items(),
        key=lambda kv: kv[1].get("updated", kv[1].get("created", "")),
        reverse=True,
    )
    return ordered


def load_contents(session_id):
    """Muat isi riwayat sesi; None jika tidak ada."""
    data = _load_all()
    sess = data.get("sessions", {}).get(session_id)
    if not sess:
        return None
    return sess.get("contents", [])


def delete_session(session_id):
    data = _load_all()
    sessions = data.get("sessions", {})
    if session_id not in sessions:
        return False
    del sessions[session_id]
    if data.get("active") == session_id:
        remaining = list(sessions.keys())
        data["active"] = remaining[0] if remaining else None
    return _save_all(data)


def delete_all_sessions():
    """Hapus semua sesi. Mengembalikan True bila berhasil."""
    data = _load_all()
    data["sessions"] = {}
    data["active"] = None
    return _save_all(data)


def find_sessions(query):
    """Cari id sesi berdasarkan id/nama. Mengembalikan daftar id.

    Id yang cocok persis dikembalikan dulu (1 hasil); selain itu cari
    nama yang mengandung query.
    """
    q = (query or "").strip().lower()
    if not q:
        return []
    sessions = _load_all().get("sessions", {})
    ids = []
    for sid, meta in sessions.items():
        if sid == q or sid.lower() == q:
            return [sid]
    for sid, meta in sessions.items():
        name = (session_name(meta) or "").lower()
        if q in name or name.startswith(q):
            ids.append(sid)
    return ids


def format_sessions_list():
    ordered = list_sessions()
    if not ordered:
        return f"{fmt.BORDER_V} {colors.C_WARNING}Belum ada sesi tersimpan.{colors.C_RESET}"
    active = get_active_session()
    lines = []
    lines.append(fmt.separator_line("sessions"))
    lines.append("")
    for sid, meta in ordered:
        name = session_name(meta) or sid
        marker = f"{colors.C_SUCCESS}●{colors.C_RESET}" if sid == active else f"{colors.C_FG_DIM}○{colors.C_RESET}"
        n = len(meta.get("contents", []))
        lines.append(f" {marker} {colors.C_BOLD}{name}{colors.C_RESET}  {colors.C_FG_DIM}({n} pesan){colors.C_RESET}")
    lines.append("")
    lines.append(fmt.border_bottom())
    lines.append("")
    lines.append(f"{colors.C_FG_DIM}Gunakan:{colors.C_RESET} {colors.C_BOLD}/session{colors.C_RESET}  |  {colors.C_BOLD}/session baru{colors.C_RESET}  |  {colors.C_BOLD}/session hapus <nama>{colors.C_RESET}  |  {colors.C_BOLD}/session hapus semua{colors.C_RESET}")
    return "\n".join(lines)


def print_session_preview(session_id, contents):
    meta = get_meta(session_id)
    title = session_name(meta) or session_id
    print()
    print(fmt.separator_line(f"session: {title}"))
    print()
    shown = contents[-10:]
    for item in shown:
        role = item.get("role")
        parts = item.get("parts", [])
        for p in parts:
            if "text" in p:
                text = p["text"].replace("\n", " ")[:80]
                if role == "user":
                    print(f"{fmt.BORDER_V} {colors.C_USER_FG}{colors.C_BOLD}You{colors.C_RESET}  {text}")
                else:
                    print(f"{fmt.BORDER_V} {colors.C_AI_FG}{colors.C_BOLD}AI{colors.C_RESET}  {colors.C_FG}{text}{colors.C_RESET}")
    print()
    print(fmt.border_bottom())
    print()


def handle_sessions_cli(action, contents):
    """Handler perintah /session dari main loop.

    Returns:
        tuple (contents_baru, lanjutkan) — contents_baru adalah daftar riwayat,
        lanjutkan True bila harus lanjut ke prompt berikutnya.
    """
    cmd = (action or "").strip()

    if not cmd:
        # /session  -> buka panel interaktif untuk memilih sesi
        return pick_session_interactive(contents)

    if cmd.lower() in ("baru", "new", "bersih", "clear"):
        # Mulai sesi baru: simpulkan sesi aktif yang lama, buat id baru.
        return [], True

    if cmd.lower() in ("hapus", "delete", "del", "rm"):
        return contents, "hapus"  # tanda butuh argumen tambahan

    # Anggap <id> untuk memuat
    loaded = load_contents(cmd)
    if loaded is None:
        print(f"{fmt.BORDER_V} {colors.C_ERROR}Sesi '{cmd}' tidak dikenal. Ketik /session untuk daftar.{colors.C_RESET}\n")
        return contents, True
    return loaded, True


def pick_session_interactive(current_contents):
    """Panel interaktif pilih sesi pakai tombol atas/bawah + Enter.

    Returns:
        tuple (contents_baru, lanjutkan):
        - (None, False)   -> batal / sesi tidak berubah
        - ("__new__", ...) -> mau buat sesi baru (ditangani main loop)
        - (contents, True) -> muat isi sesi terpilih
    """
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, Window, HSplit, FormattedTextControl
    from prompt_toolkit.layout.containers import WindowAlign

    ordered = list_sessions()
    if not ordered:
        return None, False

    # Urutan pilihan panel: [sesi-sesi..., __NEW__]
    options = [(sid, meta) for sid, meta in ordered]
    new_label = "__new__"
    options.append((new_label, {"contents": current_contents}))

    active = get_active_session()
    idx = 0
    for i, (sid, _) in enumerate(options):
        if sid == active:
            idx = i
            break

    result = {"value": None}

    # Prompt-toolkit styles (bukan ANSI mentah, supaya tidak tampil kode escape).
    ST_TITLE  = "bold #ff9f0a"
    ST_SEL    = "#ff9f0a bold"
    ST_ACTIVE = "#30d158 bold"
    ST_ID     = "bold"
    ST_DIM    = "#9a9898"
    ST_META   = "#9a9898"

    def render():
        frags = []

        def row(style, text):
            frags.append((style, text))

        row(ST_TITLE, "  ≡ PILIH SESI\n\n")

        for i, (sid, meta) in enumerate(options):
            name = session_name(meta) or sid
            if sid == new_label:
                row(ST_SEL if i == idx else "", "▶" if i == idx else " ")
                row("#30d158" if i == idx else ST_META, "  ＋ Buat sesi baru\n")
                continue
            row(ST_SEL if i == idx else "", "▶" if i == idx else " ")
            if sid == active:
                row(ST_ACTIVE, f"● {name}")
            else:
                row(ST_ID, f"  {name}")
            n = len(meta.get("contents", []))
            row(ST_META, f"  ({n} pesan)")
            row("", "\n")

        row("", "\n")
        row(ST_META, "  ↑/↓ j/k gerak · Enter pilih · d hapus · q tutup")
        return frags

    control = FormattedTextControl(text=render())

    kb = KeyBindings()

    def move(delta):
        nonlocal idx
        idx = (idx + delta) % len(options)
        control.text = render()

    @kb.add("up")
    @kb.add("k")
    def _(event):
        move(-1)

    @kb.add("down")
    @kb.add("j")
    def _(event):
        move(1)

    def _refresh_options():
        nonlocal idx, options, active
        ordered = list_sessions()
        options = [(s, m) for s, m in ordered]
        options.append((new_label, {"contents": current_contents}))
        active = get_active_session()
        if idx >= len(options):
            idx = len(options) - 1
        control.text = render()

    @kb.add("enter")
    def _(event):
        result["value"] = options[idx][0]
        event.app.exit()

    @kb.add("d")
    def _(event):
        sid = options[idx][0]
        if sid == new_label:
            return
        delete_session(sid)
        _refresh_options()

    @kb.add("q")
    @kb.add("c-c")
    @kb.add("escape")
    def _(event):
        result["value"] = None
        event.app.exit()

    layout = Layout(Window(control, wrap_lines=True, align=WindowAlign.LEFT))
    app = Application(layout=layout, key_bindings=kb, full_screen=False)

    try:
        app.run()
    except Exception:
        # Fallback bila TTY tidak mendukung prompt_toolkit
        print(format_sessions_list())
        c = input(f"{fmt.BORDER_V} {colors.C_BOLD}Pilih nomor / id sesi{colors.C_RESET} > ").strip()
        if not c:
            return None, False
        if c.isdigit() and 1 <= int(c) <= len(ordered):
            c = ordered[int(c) - 1][0]
        loaded = load_contents(c)
        if loaded is None:
            return None, False
        save_session(c, loaded)  # tandai sebagai sesi aktif
        return loaded, True

    value = result["value"]
    if value is None or value == new_label:
        # None => batal; new_label => buat sesi baru (isi kosong)
        if value == new_label:
            return [], True
        return None, False

    loaded = load_contents(value)
    if loaded is None:
        return None, False
    save_session(value, loaded)  # tandai sebagai sesi aktif
    return loaded, True
