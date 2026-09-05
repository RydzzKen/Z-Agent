"""OpenCode-style Unicode formatting helpers for Z-Agent."""
import os
import re
from . import colors


# ── Unicode symbols ──────────────────────────────────────────────────
BORDER_V    = "┃"    # heavy vertical line
CORNER_BL   = "╹"    # bottom-left corner
HALF_TOP    = "▀"    # upper half block
ARROW_READ  = "→"    # read operation
ARROW_WRITE = "←"    # write operation
COMPLETE    = "▣"    # completion marker
PROGRESS_ON = "■"    # filled progress
PROGRESS_OFF= "⬝"    # empty progress
TIP_DOT     = "●"    # tip marker
SEPARATOR   = "─"    # horizontal line


def _terminal_width():
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 80


def _clean(s):
    """Remove ANSI escape sequences for length math."""
    return re.sub(r"\033\[[0-9;]*m", "", s)


def border_line(width=None):
    """Full-width border line of ─ characters."""
    w = width or _terminal_width()
    return f"{colors.C_BORDER}{SEPARATOR * w}{colors.C_RESET}"


def border_bottom(width=None):
    """OpenCode-style bottom frame: ╹▀▀▀▀..."""
    w = width or _terminal_width()
    return f"{colors.C_BORDER}{CORNER_BL}{HALF_TOP * (w - 1)}{colors.C_RESET}"


def input_line(label_fg=None):
    """OpenCode-style prompt prefix: ┃ You  __"""
    label = f"{colors.C_USER_FG}{colors.C_BOLD}You{colors.C_RESET}"
    return f"{colors.C_BORDER}{BORDER_V}{colors.C_RESET} {label} "


def user_line(text):
    """User message inside border."""
    return f"{colors.C_BORDER}{BORDER_V}{colors.C_RESET} {colors.C_USER_FG}{colors.C_BOLD}You{colors.C_RESET}  {colors.C_FG}{text}{colors.C_RESET}"


def ai_line(text):
    """AI message line inside border."""
    return f"{colors.C_BORDER}{BORDER_V}{colors.C_RESET} {colors.C_FG}{text}{colors.C_RESET}"


def thinking_line(text):
    """Thinking/reasoning output."""
    return (
        f"{colors.C_BORDER}{BORDER_V}{colors.C_RESET} "
        f"{colors.C_THINK_FG}{colors.C_DIM}{text}{colors.C_RESET}"
    )


def tool_call_line(tool_name, args, cycle=None, max_cycles=None, is_read=False):
    """Tool call line like OpenCode:
    ┃ → read_file(path="main.py")
    ┃ ← write_file(path="test.py")
    """
    arrow = colors.C_READ_FG + ARROW_READ if is_read else colors.C_WRITE_FG + ARROW_WRITE
    cycle_tag = ""
    if cycle is not None and max_cycles is not None:
        cycle_tag = f" {colors.C_FG_DIM}({cycle}/{max_cycles}){colors.C_RESET}"
    args_str = _format_args(args)
    return (
        f"{colors.C_BORDER}{BORDER_V}{colors.C_RESET} "
        f"{arrow} {colors.C_TOOL_FG}{colors.C_BOLD}{tool_name}{colors.C_RESET}"
        f"{args_str}{cycle_tag}"
    )


def tool_result_line(result, max_len=140):
    """Compact one-line tool result."""
    s = str(result).replace("\n", " ").strip()
    if len(s) > max_len:
        s = s[:max_len] + "…"
    return (
        f"{colors.C_BORDER}{BORDER_V}{colors.C_RESET} "
        f"{colors.C_FG_DIM}{s}{colors.C_RESET}"
    )


def completion_line(agent="Z-Agent", model="", duration=None):
    """Completion marker: ┃ ▣ Z-Agent · gemini-2.5-flash · 10.2s"""
    parts = [f"{colors.C_COMPLETE_FG}{COMPLETE} {colors.C_BOLD}{agent}{colors.C_RESET}"]
    if model:
        parts.append(f"{colors.C_FG_DIM}·{colors.C_RESET} {colors.C_FG}{model}{colors.C_RESET}")
    if duration is not None:
        parts.append(f"{colors.C_FG_DIM}· {duration:.1f}s{colors.C_RESET}")
    return f"{colors.C_BORDER}{BORDER_V}{colors.C_RESET} " + " ".join(parts)


def separator_line(label="", width=None):
    """OpenCode-style divider: ─── label ───"""
    w = width or _terminal_width()
    if not label:
        return border_line(width)
    label_full = f" {label} "
    dash_each = (w - len(label_full)) // 2
    rest = w - dash_each - len(label_full)
    return (
        f"{colors.C_BORDER}{SEPARATOR * dash_each}"
        f"{colors.C_FG}{label_full}"
        f"{colors.C_BORDER}{SEPARATOR * rest}"
        f"{colors.C_RESET}"
    )


def info_row(label, value, label_width=14):
    """Key-value row for info panels."""
    pad = " " * (label_width - len(label))
    return f"{colors.C_YELLOW}{label}{pad}{colors.C_RESET} {colors.C_FG}{value}{colors.C_RESET}"


def command_row(cmd, desc):
    """Command + description row for menus."""
    return f" {colors.C_BOLD}{colors.C_INFO}{cmd:<10}{colors.C_RESET} {colors.C_FG_DIM}{desc}{colors.C_RESET}"


def _format_args(args):
    """Format tool args for inline display, e.g. (path="main.py")."""
    if not args:
        return ""
    parts = []
    for k, v in args.items():
        val = repr(v) if isinstance(v, str) else str(v)
        if len(val) > 40:
            val = val[:37] + "..."
        parts.append(f"{k}={val}")
    return f"{colors.C_FG_DIM}({', '.join(parts)}){colors.C_RESET}"