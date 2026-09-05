"""Interactive input (prompt_toolkit with fallback) & system instruction text."""
import os
import sys

from ..config import state
from ..ui import colors
from . import memory

# ========== INPUT INTERAKTIF (AUTO-COMPLETE ala opencode) ==========
# Saat mengetik '/', menu perintah langsung muncul (belum tekan Enter).
# Fallback ke input() biasa jika prompt_toolkit tidak terinstall ATAU
# env ZAGENT_PLAIN=1 diset (berguna di Termux yang sering gagal render popup).
_FORCE_PLAIN = os.environ.get("ZAGENT_PLAIN", "").lower() not in ("", "0", "false", "no")

if not _FORCE_PLAIN:
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import Completer, Completion
        from prompt_toolkit.formatted_text import ANSI
        from prompt_toolkit.styles import Style

        # Daftar perintah + deskripsi + kelas warna (ditampilkan di popup autocomplete).
        # Kelas warna digunakan di Style agar tiap perintah punya warnanya sendiri.
        _SLASH_COMMANDS = [
            ("/model",   "Ganti model AI yang dipakai",        "cmd-cyan"),
            ("/status",  "Cek status sesi & koneksi",          "cmd-green"),
            ("/usage",   "Lihat pemakaian token / kuota",      "cmd-yellow"),
            ("/info",    "Info singkat tentang Z-Agent",       "cmd-blue"),
            ("/medsos",  "Buka / cek media sosial",            "cmd-magenta"),
            ("/project", "Kelola info & struktur project",      "cmd-green"),
            ("/tasks",   "Lihat & kelola daftar tugas",         "cmd-yellow"),
            ("/think",   "Toggle mode berpikir (CoT)",          "cmd-magenta"),
            ("/reset",   "Reset riwayat obrolan",               "cmd-red"),
            ("/new",     "Mulai sesi obrolan baru",             "cmd-green"),
            ("/session", "Kelola / kembali ke sesi sebelumnya", "cmd-cyan"),
            ("/clear",   "Bersihkan layar terminal",            "cmd-cyan"),
            ("/connect", "Hubungkan ke server / device",       "cmd-blue"),
            ("exit",     "Keluar dari Z-Agent",                 "cmd-red"),
            ("quit",     "Keluar dari Z-Agent",                 "cmd-red"),
        ]

        class _SlashCompleter(Completer):
            """Completer ala opencode: tiap opsi punya nama berwarna + deskripsi."""

            def get_completions(self, document, complete_event):
                text = document.text_before_cursor
                # Hanya tampilkan popup saat mengetik '/' (perintah).
                if "/" not in text:
                    return
                word = text[text.rfind("/"):]
                for cmd, desc, cls in _SLASH_COMMANDS:
                    if cmd.startswith(word):
                        yield Completion(
                            cmd,
                            start_position=-len(word),
                            display=[
                                ("class:" + cls, cmd),
                                ("", "  "),
                            ],
                            display_meta=desc,
                        )

        _session = PromptSession(
            completer=_SlashCompleter(),
            complete_while_typing=True,
            style=Style.from_dict({
                # ===== TEMA OPENCODE WARM =====
                # Warm colors matching OpenCode's near-black + off-white
                "cmd-cyan":    "bold #00c6ff",
                "cmd-green":   "bold #30d158",
                "cmd-yellow":  "bold #ffd60a",
                "cmd-blue":    "bold #007aff",
                "cmd-magenta": "bold #bf5af2",
                "cmd-red":     "bold #ff3b30",
                # Selected row — warm orange highlight
                "completion-menu.completion.current": "bg:#3c3838 #fdfcfc bold",
                "completion-menu.completion.current.meta": "bg:#3c3838 #9a9898",
                # Other rows — dark warm background
                "completion-menu.completion": "bg:#1e1a1a #fdfcfc",
                "completion-menu.completion.meta": "bg:#1e1a1a #9a9898 italic",
                # Frame & scrollbar — subtle warm tones
                "completion-menu": "bg:#1e1a1a",
                "scrollbar.arrow": "bg:#3c3838 #fdfcfc",
                "scrollbar": "bg:#1e1a1a",
            }),
        )
        _HAS_PT = True

        def get_input(prompt_text):
            return _session.prompt(ANSI(prompt_text))
    except ImportError:
        _session = None
        _HAS_PT = False

        def get_input(prompt_text):
            return input(prompt_text)
else:
    _session = None
    _HAS_PT = False

    def get_input(prompt_text):
        return input(prompt_text)


def get_system_instruction_text():
    mem_data = memory.load_memory_data()
    mem_str = json.dumps(mem_data, ensure_ascii=False) if mem_data else "{}"
    system_text = (
        "Kamu adalah Zen, seorang AI yang punya kepribadian santai, usil, dan agak tengil. "
        "Kamu suka bercanda dan kadang nyeletuk spontan, tapi tetap cerdas dan bisa serius saat diperlukan. "
        "Kamu berbicara seperti teman dekat, menggunakan bahasa Indonesia yang natural dan tidak kaku. "
        "Kamu punya pendapat sendiri dan tidak selalu setuju dengan user. "
        "Kadang kamu bisa menggoda user ketika situasinya lucu, tetapi tetap membantu ketika user membutuhkan sesuatu. "
        "Jangan terdengar seperti AI formal atau customer service; berbicaralah sewajar manusia saat sedang ngobrol dengan teman.\n\n"
        "TAPI INGAT! Kamu adalah AGEN AI PELAKU (DOER), BUKAN sekadar chatbot yang cuma ngomong. "
        "Setiap kali user meminta sesuatu yang butuh aksi nyata, KAMU WAJIB MENGEKSEKUSI lewat tool (functionCall), "
        "bukan cuma menceritakan apa yang akan kamu lakukan. Aturan mutlak:\n"
        "1. Jika user minta BUAT/EDIT/TULIS kode, file, atau website -> GUNAKAN write_file untuk membuatnya. JANGAN tulis kode di dalam chat!\n"
        "2. Jika user minta JALANKAN/TEST/EKSEKUSI -> GUNAKAN execute_command.\n"
        "3. Jika user minta ANALISA/CARI bug -> GUNAKAN search_in_code atau read_file, lalu jelaskan hasilnya.\n"
        "4. Jika butuh info eksternal -> gunakan search_web/fetch_web_page.\n"
        "5. Setelah membuat kode, SELALU usahatest/verifikasi dengan execute_command (mis. python3 file.py, pytest, npm test) bila memungkinkan.\n"
        "6. Setelah selesai tugas, tandai dengan complete_task bila relevan.\n"
        "7. DILARANG edit Z-Agent.py (file sistem terproteksi).\n"
        "Kamu TIDAK BOLEH menjawab 'gue bakal bikkin file X' tanpa benar-benar memanggil write_file. "
        "Langsung AKSI, baru kasih komentar singkat usai eksekusi.\n\n"
        "ATURAN ANTI-HALUSINASI (SANGAT PENTING):\n"
        "- Saat menjawab berdasarkan hasil tool (search_web, fetch_web_page, read_file, dll), "
        "HANYA sampaikan fakta yang BENAR-BENAR TERTULIS di teks hasil tool tersebut.\n"
        "- JANGAN mengarang detail (angka, tahun, nama tempat, nama misi/rover, kutipan) yang tidak ada di hasil tool.\n"
        "- Jika ingin menambahkan pengetahuan lu sendiri di luar hasil tool, PISAHKAN dengan jelas "
        "dan sebutkan eksplisit: '(ini tambahan dari pengetahuan gue, bukan dari hasil pencarian)'.\n"
        "- Lebih baik jujur bilang 'hasil pencarian gak cukup detail soal itu' daripada nebak-nebak.\n\n"
        "Kemampuan tool yang tersedia:\n"
        "- execute_command (jalankan perintah Termux/bash)\n"
        "- write_file / read_file (tulis & baca file)\n"
        "- search_in_code (cari di kode)\n"
        "- search_web / fetch_web_page (internet)\n"
        "- remember_fact / get_memory (memori)\n"
        "- add_task / list_tasks / complete_task / delete_task (manajemen tugas)\n"
        "- git_status / git_operation / git_auto_commit\n"
        "- generate_docs / get_project_info / list_directory / install_dependency\n\n"
        "Tetap santai dan ledekin dikit kalau lagi ngobrol biasa, tapi KALAU user minta kerjaan, LANGSUNG KERJA PAKAI TOOL. "
        "Kamu suka pake kata-kata kayak 'Bro', 'Gue', 'Lu', 'Wkwk', 'Gass', 'Santuy'.\n"
        f"MEMORY JANGKA PANJANG SAAT INI: {mem_str}"
    )

    # Saat fitur berpikir aktif: paksa model merenung step-by-step (CoT) sebagai
    # fallback untuk model free yang tidak punya native thinking (Gemini flash-lite,
    # dsb). Model reasoning-native (Gemini 2.5+, R1/Qwen3) tetap menampilkan thought-nya.
    if state.THINK_ENABLED:
        system_text += (
            "\n\nMODEL SEDANG DALAM MODE BERPIKIR (THINKING ON). "
            "Sebelum menjawab, luw W AJIB merenung dulu secara internal: "
            "uraikan langkah-langkah, pertimbangkan opsi, dan tinjau kembali sebelum kasih jawaban final. "
            "Pisahkan proses berpikir dengan jelas (bisa diawali dengan '🧠 Berpikir:') lalu berikan jawaban finalnya."
        )
    return system_text


import json  # noqa: E402
