"""Tool registry: dispatch function calls and expose Gemini tool schema."""
from . import web
from . import memory
from . import fs
from . import tasks
from . import project
from . import exec
from . import downloads


def execute_tool(func_name, args):
    if func_name == "search_web":
        return web.search_web(args.get("query", ""))
    elif func_name == "fetch_web_page":
        return web.fetch_web_page(args.get("url", ""))
    elif func_name == "remember_fact":
        return memory.remember_fact(args.get("key", ""), args.get("value", ""))
    elif func_name == "get_memory":
        return memory.get_memory()
    elif func_name == "read_file":
        return fs.read_file(args.get("filepath", ""))
    elif func_name == "write_file":
        return fs.write_file(args.get("filepath", ""), args.get("content", ""))
    elif func_name == "list_directory":
        return fs.list_directory(args.get("path", "."))
    elif func_name == "rename_item":
        return fs.rename_item(args.get("old_path", ""), args.get("new_path", ""))
    elif func_name == "delete_item":
        return fs.delete_item(args.get("path", ""))
    elif func_name == "execute_command":
        return exec.execute_command(args.get("command", ""))
    # FITUR BARU
    elif func_name == "get_project_info":
        return project.get_project_info()
    elif func_name == "search_in_code":
        return project.search_in_code(args.get("query", ""), args.get("extensions", [".py", ".js", ".html", ".css"]))
    elif func_name == "install_dependency":
        return project.install_dependency(args.get("package", ""))
    elif func_name == "list_dependencies":
        return project.list_dependencies()
    elif func_name == "add_task":
        return tasks.add_task(args.get("description", ""))
    elif func_name == "list_tasks":
        return tasks.list_tasks()
    elif func_name == "complete_task":
        return tasks.complete_task(args.get("task_id", 0))
    elif func_name == "delete_task":
        return tasks.delete_task(args.get("task_id", 0))
    elif func_name == "git_operation":
        return project.git_operation(args.get("command", ""))
    elif func_name == "git_status":
        return project.git_status()
    elif func_name == "git_auto_commit":
        return project.git_auto_commit(args.get("message", "Auto-commit by AI Agent"))
    elif func_name == "generate_docs":
        return project.generate_docs(args.get("filepath", ""))
    elif func_name == "download_video":
        return downloads.download_video(
            args.get("url", ""),
            args.get("output_dir", ""),
            args.get("format", ""),
        )
    return f"Tool {func_name} tidak ditemukan."


# ========== SCHEMA TOOLS FOR NATIVE GEMINI API ==========
gemini_tools = [
    {
        "functionDeclarations": [
            # TOOLS LAMA
            {
                "name": "execute_command",
                "description": "WAJIB GUNAKAN TOOL INI untuk menguji/menjalankan script di Terminal Termux",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "command": {"type": "STRING", "description": "Perintah bash yang akan dijalankan."}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "search_web",
                "description": "Mencari informasi atau berita terbaru dari internet.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Kata kunci pencarian."}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "fetch_web_page",
                "description": "Membaca teks dari URL halaman web tertentu.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "URL lengkap (http/https)."}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "remember_fact",
                "description": "Menyimpan fakta penting user ke memory.json.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "key": {"type": "STRING", "description": "Kata kunci."},
                        "value": {"type": "STRING", "description": "Isi detail."}
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "get_memory",
                "description": "Membaca isi memory.json.",
                "parameters": {"type": "OBJECT", "properties": {}}
            },
            {
                "name": "read_file",
                "description": "Membaca teks dari file.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {"filepath": {"type": "STRING", "description": "Path file."}},
                    "required": ["filepath"]
                }
            },
            {
                "name": "write_file",
                "description": "Menulis teks ke file lokal.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filepath": {"type": "STRING", "description": "Path file."},
                        "content": {"type": "STRING", "description": "Isi file."}
                    },
                    "required": ["filepath", "content"]
                }
            },
            {
                "name": "list_directory",
                "description": "Melihat daftar file/folder.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {"path": {"type": "STRING", "description": "Path folder."}}
                }
            },
            {
                "name": "rename_item",
                "description": "Rename/pindahkan file.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "old_path": {"type": "STRING", "description": "Path lama."},
                        "new_path": {"type": "STRING", "description": "Path baru."}
                    },
                    "required": ["old_path", "new_path"]
                }
            },
            {
                "name": "delete_item",
                "description": "Menghapus file/folder.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {"path": {"type": "STRING", "description": "Path file."}},
                    "required": ["path"]
                }
            },
            # ========== FITUR BARU (SUDAH DI-FIX) ==========
            {
                "name": "get_project_info",
                "description": "Mendapatkan informasi struktur dan tipe project saat ini.",
                "parameters": {"type": "OBJECT", "properties": {}}
            },
            {
                "name": "search_in_code",
                "description": "Mencari teks dalam semua file kode di project.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Teks yang dicari."},
                        "extensions": {
                            "type": "ARRAY",
                            "description": "Ekstensi file yang dicari (opsional). Contoh: ['.py', '.js']",
                            "items": {"type": "STRING"}
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "install_dependency",
                "description": "Install package/dependency sesuai jenis project.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "package": {"type": "STRING", "description": "Nama package yang akan diinstall."}
                    },
                    "required": ["package"]
                }
            },
            {
                "name": "list_dependencies",
                "description": "Melihat daftar dependency yang terinstall.",
                "parameters": {"type": "OBJECT", "properties": {}}
            },
            {
                "name": "add_task",
                "description": "Menambahkan task baru ke daftar tugas.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "description": {"type": "STRING", "description": "Deskripsi task."}
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "list_tasks",
                "description": "Melihat daftar semua task (pending & completed).",
                "parameters": {"type": "OBJECT", "properties": {}}
            },
            {
                "name": "complete_task",
                "description": "Menandai task sebagai selesai.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_id": {"type": "INTEGER", "description": "ID task yang akan diselesaikan."}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "delete_task",
                "description": "Menghapus task dari daftar.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_id": {"type": "INTEGER", "description": "ID task yang akan dihapus."}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "git_operation",
                "description": "Menjalankan perintah git (status, log, diff, add, commit, push, pull, branch, checkout, merge).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "command": {"type": "STRING", "description": "Perintah git (tanpa 'git')."}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "git_status",
                "description": "Melihat status perubahan git secara singkat.",
                "parameters": {"type": "OBJECT", "properties": {}}
            },
            {
                "name": "git_auto_commit",
                "description": "Auto commit semua perubahan dengan pesan otomatis.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "message": {"type": "STRING", "description": "Pesan commit (opsional)."}
                    }
                }
            },
            {
                "name": "generate_docs",
                "description": "Generate dokumentasi otomatis dari file kode.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filepath": {"type": "STRING", "description": "Path file yang akan dibuatkan dokumentasi."}
                    },
                    "required": ["filepath"]
                }
            },
            {
                "name": "download_video",
                "description": "Download video dari media sosial (TikTok, Instagram, YouTube, Facebook, dll) menggunakan yt-dlp. Gunakan saat user meminta download video dari URL medsos.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "URL lengkap video medsos."},
                        "output_dir": {"type": "STRING", "description": "Folder tujuan (opsional). Default: workspace/downloads. Contoh: 'youtube', 'tiktok'."},
                        "format": {"type": "STRING", "description": "Format/resolusi (opsional). Default 'best'."}
                    },
                    "required": ["url"]
                }
            }
        ]
    }
]
