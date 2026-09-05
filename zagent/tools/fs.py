"""Filesystem tools: read/write/list/rename/delete with workspace sandboxing."""
import os
import shutil

from ..config import state
from ..ui import colors


def _resolve_path(target_path):
    """Resolve path ke dalam WORKSPACE_DIR (folder workspace saja)."""
    if os.path.isabs(target_path):
        return os.path.abspath(target_path)
    return os.path.abspath(os.path.join(state.WORKSPACE_DIR, target_path))


def is_safe_path(target_path):
    abs_target = _resolve_path(target_path)
    return abs_target == state.WORKSPACE_DIR or abs_target.startswith(state.WORKSPACE_DIR + os.sep)


def read_file(filepath):
    filepath = _resolve_path(filepath)
    if not is_safe_path(filepath):
        return "Error Security: Akses di luar direktori kerja ditolak!"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            if len(content) > 5000:
                content = content[:5000] + "\n... (file terlalu besar, hanya 5000 karakter pertama)"
            return f"--- ISI FILE '{filepath}' ---\n{content}"
    except Exception as e:
        return f"Error membaca file: {e}"


def write_file(filepath, content):
    filepath = _resolve_path(filepath)
    if not is_safe_path(filepath):
        return "Error Security: Akses di luar direktori kerja ditolak!"

    # ===== PROTEKSI FILE PENTING =====
    filename = os.path.basename(filepath).lower()
    protected_files = ["agent2.py", "bot.py", "run.sh", "memory.json", "tasks.json", "Z-Agent.py"]
    if filename in protected_files:
        return f"❌ Error Protection: Dilarang mengedit file sistem ({filename})!"
    # =================================

    try:
        folder = os.path.dirname(filepath)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Berhasil menulis file: {filepath}"
    except Exception as e:
        return f"Error menulis file: {e}"


def list_directory(path="."):
    target_path = _resolve_path(path if path else ".")
    if not is_safe_path(target_path):
        return "Error Security: Akses di luar direktori kerja ditolak!"
    try:
        if not os.path.exists(target_path):
            return f"Error: Path '{target_path}' tidak ditemukan."
        items = os.listdir(target_path)
        if not items:
            return f"Folder '{target_path}' kosong."
        result = [f"--- ISI FOLDER '{target_path}' ---"]
        for item in sorted(items):
            if item.startswith('.'):
                continue
            full = os.path.join(target_path, item)
            if os.path.isdir(full):
                result.append(f"📁 {item}/")
            else:
                size = os.path.getsize(full)
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f}KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f}MB"
                result.append(f"📄 {item} ({size_str})")
        return "\n".join(result)
    except Exception as e:
        return f"Error memeriksa folder: {e}"


def rename_item(old_path, new_path):
    old_path = _resolve_path(old_path)
    new_path = _resolve_path(new_path)
    if not is_safe_path(old_path) or not is_safe_path(new_path):
        return "Error Security: Akses di luar direktori kerja ditolak!"
    try:
        if not os.path.exists(old_path):
            return f"Error: '{old_path}' tidak ditemukan."
        os.rename(old_path, new_path)
        return f"Berhasil merename '{old_path}' menjadi '{new_path}'"
    except Exception as e:
        return f"Error merename: {e}"


def delete_item(path):
    path = _resolve_path(path)
    if not is_safe_path(path):
        return "Error Security: Akses di luar direktori kerja ditolak!"

    filename = os.path.basename(path).lower()
    protected_files = ["bot.py", "agent2.py", "run.sh", "memory.json", "tasks.json", "Z-Agent.py"]
    if filename in protected_files:
        return f"Error Protection: Dilarang menghapus file sistem utama ({filename})!"

    try:
        if not os.path.exists(path):
            return f"Error: '{path}' tidak ditemukan."
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return f"Berhasil menghapus: '{path}'"
    except Exception as e:
        return f"Error menghapus: {e}"
