"""CLI banner & screen helpers — OpenCode style."""
import os
import shutil

from ..config import state
from . import colors
from . import format as fmt


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    clear_screen()
    w = fmt._terminal_width()
    c = colors

    # ASCII art logo — compact block style inspired by OpenCode
    logo_lines = [
        "██████╗ ███████╗ █████╗  ██████╗  ██████╗  ███████╗",
        "██╔═══╝ ██╔════╝██╔══██╗██╔═══██╗██╔═══██╗ ██╔════╝",
        "███████╗ █████╗  ███████║██║   ██║██║   ██║ █████╗  ",
        "╚════██║ ██╔══╝  ██╔══██║██║   ██║██║   ██║ ██╔══╝  ",
        "███████║ ███████╗██║  ██║╚██████╔╝╚██████╔╝ ███████╗",
        "╚══════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝  ╚══════╝",
    ]

    # Print logo centered with warm accent
    for line in logo_lines:
        pad = max(0, (w - len(line)) // 2)
        print(f"{' ' * pad}{c.C_ACCENT}{c.C_BOLD}{line}{c.C_RESET}")

    print()

    # Model info — right-aligned style
    model_str = f"{state.PROVIDER['name']}/{state.MODEL_NAME}"
    tag = f"  {c.C_FG_DIM}{model_str}{c.C_RESET}"
    print(f"{c.C_FG_DIM}agent{c.C_RESET}  {c.C_FG}{state.MODEL_NAME}{c.C_RESET}{tag}")

    print()

    # Quick hints
    hints = [
        f"{c.C_FG_DIM}Ask anything...{c.C_RESET}",
    ]
    for h in hints:
        pad = max(0, (w - 50) // 2)
        print(f"{' ' * pad}{h}")

    print()

    # Commands reference — compact grid
    print(fmt.separator_line("commands"))
    print()

    commands = [
        ("/status",   "Status agent & koneksi"),
        ("/model",    "Ganti model AI"),
        ("/connect",  "Hubungkan provider & API key"),
        ("/think",    "Mode berpikir ON/OFF"),
        ("/session",  "Kelola sesi percakapan"),
        ("/tasks",    "Lihat daftar tugas"),
        ("/project",  "Info project saat ini"),
        ("/usage",    "Ringkasan pemakaian token"),
        ("/info",     "Profil agent"),
        ("/medsos",   "Media sosial developer"),
        ("/new",      "Mulai sesi baru"),
        ("/reset",    "Reset riwayat percakapan"),
        ("/clear",    "Bersihkan layar"),
        ("exit",      "Keluar dari Z-Agent"),
    ]

    # Print commands in two columns
    col_w = w // 2
    for i in range(0, len(commands), 2):
        left_cmd, left_desc = commands[i]
        left = f" {c.C_BOLD}{c.C_INFO}{left_cmd:<10}{c.C_RESET} {c.C_FG_DIM}{left_desc}{c.C_RESET}"
        if i + 1 < len(commands):
            right_cmd, right_desc = commands[i + 1]
            right = f" {c.C_BOLD}{c.C_INFO}{right_cmd:<10}{c.C_RESET} {c.C_FG_DIM}{right_desc}{c.C_RESET}"
            # pad left to col_w
            import re
            clean_left = re.sub(r'\033\[[0-9;]*m', '', left)
            clean_right = re.sub(r'\033\[[0-9;]*m', '', right)
            pad = max(0, col_w - len(clean_left))
            print(f"{left}{' ' * pad}{right}")
        else:
            print(left)

    print()
    print(fmt.border_bottom())
    print()
