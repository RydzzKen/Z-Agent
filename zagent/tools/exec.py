"""Command execution tool with sandboxing & security guards."""
import re
import subprocess

from ..config import state
from ..ui import colors


def execute_command(command):
    """Jalankan perintah shell/bash sederhana dan kembalikan output/error-nya."""

    # ===== PROTEKSI REDIRECT & OVERWRITE FILE PENTING =====
    dangerous_patterns = [
        r">\s*agent2\.py",
        r">\s*bot\.py",
        r">\s*memory\.json",
        r">\s*tasks\.json",
        r">\s*run\.sh",
        r">\s*\.env",
        r">\s*\.bashrc",
        r">\s*\.zshrc",
        r"cat\s+.*>\s*agent2\.py",
        r"cp\s+.*\s+agent2\.py",
        r"mv\s+.*\s+agent2\.py",
        r"echo\s+.*>\s*agent2\.py",
        r"printf\s+.*>\s*agent2\.py",
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return f"❌ Error Security: Dilarang mengubah file sistem! (perintah: {command[:50]}...)"

    # Cegah redirect ke file penting pake >> (append) juga
    append_patterns = [
        r">>\s*agent2\.py",
        r">>\s*bot\.py",
        r">>\s*memory\.json",
        r">>\s*tasks\.json",
        r">>\s*run\.sh",
    ]
    for pattern in append_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return f"❌ Error Security: Dilarang append ke file sistem!"
    # =========================================================

    # Cegah perintah berbahaya
    forbidden_cmds = ["rm -rf /", "mkfs", "dd", "reboot", "shutdown", "chmod 777", "chown"]
    if any(cmd in command.lower() for cmd in forbidden_cmds):
        return "Error Security: Perintah berbahaya ditolak!"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=state.WORKSPACE_DIR
        )

        output = result.stdout.strip()
        errors = result.stderr.strip()

        if result.returncode == 0:
            return f"[EXIT STATUS 0 (SUCCESS)]\n{output if output else 'Perintah berhasil dieksekusi tanpa output.'}"
        else:
            return f"[EXIT STATUS {result.returncode} (ERROR)]\nSTDOUT:\n{output}\nSTDERR:\n{errors}"
    except subprocess.TimeoutExpired:
        return "Error: Proses melebihi batas waktu (timeout 15 detik)."
    except Exception as e:
        return f"Error eksekusi perintah: {e}"
