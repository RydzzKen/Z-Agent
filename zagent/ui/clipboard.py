"""System clipboard helpers for Z-Agent TUI.

Supports Termux (Android), Linux (Wayland + X11), and macOS so that
``Ctrl+C``/``Ctrl+V`` inside the TUI can reach the real OS clipboard.
If no clipboard tool is available, callers fall back to Textual's local
clipboard + OSC52 escape sequence.
"""
import os
import shutil
import subprocess
import threading


def _is_termux() -> bool:
    return os.environ.get("PREFIX", "").startswith("/data/data/com.termux")


def is_clipboard_supported() -> bool:
    """Return True when a system clipboard tool is available."""
    return _copy_command() is not None and _paste_command() is not None


def _copy_command():
    if shutil.which("termux-clipboard-set"):
        return ["termux-clipboard-set"]
    if shutil.which("wl-copy"):
        return ["wl-copy"]
    if shutil.which("xclip"):
        return ["xclip", "-selection", "clipboard"]
    if shutil.which("xsel"):
        return ["xsel", "--clipboard", "--input"]
    if shutil.which("pbcopy"):
        return ["pbcopy"]
    return None


def _paste_command():
    if shutil.which("termux-clipboard-get"):
        return ["termux-clipboard-get"]
    if shutil.which("wl-paste"):
        return ["wl-paste", "--no-newline"]
    if shutil.which("xclip"):
        return ["xclip", "-selection", "clipboard", "-o"]
    if shutil.which("xsel"):
        return ["xsel", "--clipboard", "--output"]
    if shutil.which("pbpaste"):
        return ["pbpaste"]
    return None


def copy_to_system_clipboard(text: str) -> bool:
    """Write ``text`` to the system clipboard.

    Spawns the clipboard tool in the background (required for Wayland's
    ``wl-copy`` which keeps a process alive to own the selection).
    Returns ``True`` when a clipboard tool was launched.
    """
    cmd = _copy_command()
    if cmd is None:
        return False
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return False

    def feed():
        try:
            proc.communicate(input=text.encode("utf-8"), timeout=5.0)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    threading.Thread(target=feed, daemon=True).start()
    return True


def read_system_clipboard() -> str:
    """Read text from the system clipboard. Returns ``""`` on failure."""
    cmd = _paste_command()
    if cmd is None:
        return ""
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=1.0)
        return proc.stdout.decode("utf-8", errors="replace")
    except Exception:
        return ""