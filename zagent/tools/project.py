"""Project-awareness tools: detection, structure, code search, deps, git, docs."""
import os
import json

from ..config import state
from ..ui import colors
from . import exec
from . import fs
from ..llm import client


# ========== FITUR 1: PROJECT AWARENESS ==========
def detect_project_type():
    """Deteksi jenis project dari file yang ada"""
    try:
        files = os.listdir(state.WORKSPACE_DIR)

        if "package.json" in files:
            return "nodejs"
        elif "requirements.txt" in files or "setup.py" in files:
            return "python"
        elif "go.mod" in files:
            return "golang"
        elif "Cargo.toml" in files:
            return "rust"
        elif "composer.json" in files:
            return "php"
        elif "Gemfile" in files:
            return "ruby"
        elif "pom.xml" in files:
            return "java-maven"
        elif "build.gradle" in files:
            return "java-gradle"
        else:
            return "unknown"
    except Exception:
        return "unknown"


def get_project_structure(depth=2):
    """Dapatkan struktur folder dalam bentuk tree"""
    result = []
    try:
        for root, dirs, files in os.walk(state.WORKSPACE_DIR):
            level = root.replace(state.WORKSPACE_DIR, '').count(os.sep)
            if level > depth:
                continue
            indent = '  ' * level
            result.append(f"{indent}📁 {os.path.basename(root) or 'root'}/")
            sub_indent = '  ' * (level + 1)
            # Tampilkan file (max 5 per folder)
            show_files = [f for f in files if not f.startswith('.')][:5]
            for file in show_files:
                result.append(f"{sub_indent}📄 {file}")
            if len([f for f in files if not f.startswith('.')]) > 5:
                result.append(f"{sub_indent}... dan {len([f for f in files if not f.startswith('.')]) - 5} file lain")
    except Exception as e:
        return f"Error membaca struktur: {e}"
    return "\n".join(result)


def get_project_info():
    """Informasi lengkap tentang project saat ini"""
    project_type = detect_project_type()
    structure = get_project_structure(2)

    all_files = [f for f in os.listdir(state.WORKSPACE_DIR) if os.path.isfile(os.path.join(state.WORKSPACE_DIR, f))]
    all_dirs = [d for d in os.listdir(state.WORKSPACE_DIR) if os.path.isdir(os.path.join(state.WORKSPACE_DIR, d))]

    info = f"""
📊 **PROJECT INFO**
─────────────────
📍 Workspace: {state.WORKSPACE_DIR}
📦 Type: {project_type}
📁 Structure:
{structure}

📝 Files: {len(all_files)} files
📂 Folders: {len(all_dirs)} folders
"""
    return info


# ========== FITUR 2: SMART SEARCH ==========
def search_in_code(query, extensions=[".py", ".js", ".html", ".css", ".json", ".md", ".txt", ".sh"]):
    """Cari teks dalam semua file kode"""
    results = []
    try:
        for root, dirs, files in os.walk(state.WORKSPACE_DIR):
            # Skip folder tertentu
            if any(skip in root for skip in ["node_modules", ".git", "__pycache__", "venv", "env", ".venv"]):
                continue

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                # Ambil line yang match
                                lines = content.split('\n')
                                for i, line in enumerate(lines):
                                    if query.lower() in line.lower():
                                        rel_path = os.path.relpath(filepath, state.WORKSPACE_DIR)
                                        results.append(f"{rel_path}:{i + 1} -> {line.strip()[:100]}")
                    except Exception:
                        pass

            if len(results) > 20:
                break
    except Exception as e:
        return f"Error searching: {e}"

    if not results:
        return f"Tidak ditemukan '{query}' di kode"
    return "\n".join(results[:20])


# ========== FITUR 3: DEPENDENCY MANAGEMENT ==========
def install_dependency(package_name):
    """Install dependency based on project type"""
    project_type = detect_project_type()

    if project_type == "python":
        cmd = f"pip install {package_name}"
    elif project_type == "nodejs":
        cmd = f"npm install {package_name}"
    elif project_type == "golang":
        cmd = f"go get {package_name}"
    else:
        return "Tidak bisa deteksi package manager"

    return exec.execute_command(cmd)


def list_dependencies():
    """Lihat daftar dependency yang terinstall"""
    project_type = detect_project_type()

    if project_type == "python":
        return exec.execute_command("pip list")
    elif project_type == "nodejs":
        if os.path.exists("package.json"):
            try:
                with open("package.json", "r") as f:
                    data = json.load(f)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})
                    result = "📦 **Dependencies:**\n"
                    for name, ver in deps.items():
                        result += f"  - {name}: {ver}\n"
                    if dev_deps:
                        result += "\n📦 **Dev Dependencies:**\n"
                        for name, ver in dev_deps.items():
                            result += f"  - {name}: {ver}\n"
                    return result
            except Exception:
                return "Error membaca package.json"
    return "Tidak bisa mendeteksi dependencies"


# ========== FITUR 5: GIT INTEGRATION ==========
def git_operation(command):
    """Jalankan perintah git"""
    safe_git_cmds = ["status", "log", "diff", "add", "commit", "push", "pull", "branch", "checkout", "merge"]

    cmd_parts = command.split()
    if not cmd_parts or cmd_parts[0] not in safe_git_cmds:
        return f"❌ Perintah git '{cmd_parts[0]}' tidak diizinkan"

    full_cmd = f"git {command}"
    return exec.execute_command(full_cmd)


def git_auto_commit(message="Auto-commit by AI Agent"):
    """Auto commit semua perubahan"""
    result = []
    result.append(exec.execute_command("git add ."))
    result.append(exec.execute_command(f'git commit -m "{message}"'))
    return "\n".join(result)


def git_status():
    """Lihat status git"""
    return exec.execute_command("git status --short")


# ========== FITUR 6: AUTO-GENERATE DOCUMENTATION ==========
def generate_docs(filepath):
    """Generate dokumentasi dari file kode"""
    if not os.path.exists(filepath):
        return f"❌ File tidak ditemukan: {filepath}"

    content = fs.read_file(filepath)
    if "Error" in content:
        return content

    prompt = f"""
    Buat dokumentasi untuk kode berikut:

    {content[:3000]}

    Format:
    1. Deskripsi singkat
    2. Fungsi/class yang ada
    3. Parameter dan return value
    4. Contoh penggunaan
    """

    try:
        response = client.chat_with_gemini(prompt)
        doc_file = f"{filepath}.md"
        fs.write_file(doc_file, response)
        return f"✅ Dokumentasi dibuat: {doc_file}"
    except Exception as e:
        return f"❌ Error: {e}"
