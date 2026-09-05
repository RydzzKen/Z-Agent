"""Z-Agent entry point: main loop & slash-command handling."""
import time

from .config import state
from .config import provider
from .config import models
from .llm import client
from .llm import usage
from .tools import registry
from .tools import prompt
from .tools import memory
from .tools import tasks
from .tools import project
from .tools import sessions
from .ui import banner
from .ui import colors
from .ui import format as fmt


def main():
    provider.require_key()

    contents = []
    banner.print_banner()

    # Muat otomatis sesi terakhir (aktif) jika ada, agar bisa lanjut.
    last = sessions.get_active_session()
    if last:
        loaded = sessions.load_contents(last)
        if loaded:
            contents = loaded
            sessions.print_session_preview(last, contents)

    while True:
        try:
            user_input = prompt.get_input(fmt.input_line()).strip()
            if not user_input:
                continue

            # ========== PERINTAH LOKAL ==========
            if user_input.lower() in ["exit", "quit"]:
                print(f"{fmt.BORDER_V} {colors.C_FG_DIM}Sampai jumpa!{colors.C_RESET}")
                break

            if user_input == "/":
                _print_menu()
                continue

            if user_input.lower() == "/clear":
                banner.print_banner()
                print(f"{fmt.BORDER_V} {colors.C_SUCCESS}Layar dibersihkan.{colors.C_RESET}\n")
                continue

            # ========== PERINTAH SESSION ==========
            if user_input.lower() == "/session" or user_input.lower().startswith("/session "):
                action = user_input[len("/session"):].strip()

                # --- /session hapus <id> ---
                first = action.lower().split()[0] if action.split() else ""
                if first in ("hapus", "delete", "del", "rm"):
                    parts = action.split(None, 1)
                    if len(parts) < 2:
                        print(f"{fmt.BORDER_V} {colors.C_WARNING}Gunakan: /session hapus <id>{colors.C_RESET}\n")
                        continue
                    sid = parts[1].strip()
                    if sessions.delete_session(sid):
                        if sid == sessions.get_active_session():
                            contents = []
                        print(f"{fmt.BORDER_V} {colors.C_ERROR}Sesi '{sid}' dihapus.{colors.C_RESET}\n")
                    else:
                        print(f"{fmt.BORDER_V} {colors.C_WARNING}Sesi '{sid}' tidak ditemukan.{colors.C_RESET}\n")
                    continue

                # --- /session baru ---
                if action.lower() in ("baru", "new", "bersih", "clear"):
                    sessions.begin_new_session()
                    contents = []
                    print(f"{fmt.BORDER_V} {colors.C_SUCCESS}Sesi baru dimulai.{colors.C_RESET}\n")
                    continue

                # --- /session (buka panel interaktif untuk pilih sesi) ---
                if not action:
                    new_contents, _flag = sessions.pick_session_interactive(contents)
                    if new_contents == "__new__":
                        sessions.begin_new_session()
                        contents = []
                        print(f"{fmt.BORDER_V} {colors.C_SUCCESS}Sesi baru dimulai.{colors.C_RESET}\n")
                    elif isinstance(new_contents, list):
                        contents = new_contents
                        sid = sessions.get_active_session()
                        if sid:
                            sessions.print_session_preview(sid, contents)
                    # None => batal, biarkan sesi tidak berubah
                    continue

                # --- /session <id> (muat) ---
                loaded = sessions.load_contents(action)
                if loaded is None:
                    print(f"{fmt.BORDER_V} {colors.C_WARNING}Sesi '{action}' tidak ditemukan. Ketik /session untuk daftar.{colors.C_RESET}\n")
                    continue
                contents = loaded
                sessions.print_session_preview(action, contents)
                continue

            if user_input.lower() == "/reset":
                contents = []
                banner.print_banner()
                print(f"{fmt.BORDER_V} {colors.C_SUCCESS}Riwayat di-reset.{colors.C_RESET}\n")
                sid = sessions.get_active_session()
                if sid:
                    sessions.save_session(sid, contents)
                continue

            if user_input.lower() == "/new":
                contents = []
                usage.USAGE_STATS["requests"] = 0
                usage.USAGE_STATS["prompt_tokens"] = 0
                usage.USAGE_STATS["candidates_tokens"] = 0
                usage.USAGE_STATS["total_tokens"] = 0
                sessions.begin_new_session()
                banner.print_banner()
                print(f"{fmt.BORDER_V} {colors.C_SUCCESS}Sesi baru dimulai. Riwayat & usage dibersihkan.{colors.C_RESET}\n")
                continue

            if user_input.lower() == "/info":
                _print_info_panel()
                continue

            if user_input.lower() == "/medsos":
                _print_medsos_panel()
                continue

            if user_input.lower() == "/project":
                print(f"\n{project.get_project_info()}\n")
                continue

            if user_input.lower() == "/tasks":
                print(f"\n{tasks.list_tasks()}\n")
                continue

            if user_input.lower() == "/model":
                _print_model_panel()
                continue

            if user_input.lower().startswith("/model "):
                arg = user_input[7:].strip()
                _handle_model_switch(arg)
                continue

            if user_input.lower() == "/status":
                _print_status_panel(contents)
                continue

            if user_input.lower() == "/usage":
                _print_usage_panel()
                continue

            if user_input.lower().startswith("/connect"):
                _handle_connect(user_input)
                continue

            # ========== FITUR THINKING ==========
            if user_input.lower().startswith("/think"):
                _handle_think(user_input)
                continue

            # ========== PROSES AI ==========
            print(f"{fmt.BORDER_V} {colors.C_FG_DIM}...{colors.C_RESET}")
            contents.append({"role": "user", "parts": [{"text": user_input}]})

            max_cycles = 10
            cycle_count = 0
            tool_start = time.time()

            while cycle_count < max_cycles:
                cycle_count += 1
                model_content, err = client.generate_response(
                    contents, prompt.get_system_instruction_text(), registry.gemini_tools
                )

                if err is not None:
                    print(f"{fmt.BORDER_V} {colors.C_ERROR}{err}{colors.C_RESET}\n")
                    contents.pop()
                    break

                contents.append(model_content)

                parts = model_content.get("parts", [])
                function_called = False

                for part in parts:
                    if "functionCall" in part:
                        function_called = True
                        call_data = part["functionCall"]
                        fn_name = call_data["name"]
                        fn_args = call_data.get("args", {})

                        # OpenCode-style tool call line
                        is_read = fn_name in ("read_file", "list_directory", "search_in_code", "get_project_info")
                        print(fmt.tool_call_line(fn_name, fn_args, cycle_count, max_cycles, is_read))
                        result = registry.execute_tool(fn_name, fn_args)
                        print(fmt.tool_result_line(result))

                        contents.append({
                            "role": "user",
                            "parts": [
                                {
                                    "functionResponse": {
                                        "name": fn_name,
                                        "response": {"output": str(result)}
                                    }
                                }
                            ]
                        })

                if function_called:
                    continue

                # Final response
                elapsed = time.time() - tool_start
                model_short = state.MODEL_NAME.split("/")[-1] if "/" in state.MODEL_NAME else state.MODEL_NAME
                print(fmt.completion_line("Z-Agent", model_short, elapsed))
                print()

                for part in parts:
                    if part.get("thought"):
                        if state.THINK_ENABLED:
                            print(fmt.thinking_line(part.get('text', '')))
                    elif "text" in part:
                        # Print AI response with border
                        text = part["text"]
                        for line in text.split("\n"):
                            if line.strip():
                                print(fmt.ai_line(line))
                            else:
                                print(fmt.BORDER_V)
                print()
                break

            # Simpan riwayat ke sesi aktif setelah setiap pertukaran.
            sid = sessions.get_active_session()
            if not sid or sessions.load_contents(sid) is None:
                sid = sessions.new_session_id()
            sessions.save_session(sid, contents)

        except KeyboardInterrupt:
            print(f"\n{fmt.BORDER_V} {colors.C_WARNING}Proses dihentikan.{colors.C_RESET}")
            break
        except Exception as e:
            print(f"{fmt.BORDER_V} {colors.C_ERROR}Error: {e}{colors.C_RESET}")


# ── Panel helpers (slash commands) ───────────────────────────────────

def _print_menu():
    w = fmt._terminal_width()
    print()
    print(fmt.separator_line("commands"))
    print()
    commands = [
        ("/model",    "Ganti model AI"),
        ("/connect",  "Hubungkan provider & API key"),
        ("/status",   "Status agent & koneksi"),
        ("/usage",    "Ringkasan pemakaian token"),
        ("/think",    "Mode berpikir ON/OFF"),
        ("/info",     "Profil agent"),
        ("/medsos",   "Media sosial developer"),
        ("/project",  "Info project saat ini"),
        ("/tasks",    "Lihat daftar tugas"),
        ("/reset",    "Reset riwayat percakapan"),
        ("/new",      "Mulai sesi baru"),
        ("/session",  "Kelola sesi"),
        ("/clear",    "Bersihkan layar"),
        ("exit",      "Keluar dari Z-Agent"),
    ]
    col_w = w // 2
    for i in range(0, len(commands), 2):
        left = fmt.command_row(*commands[i])
        if i + 1 < len(commands):
            right = fmt.command_row(*commands[i + 1])
            pad = max(0, col_w - len(fmt._clean(left)))
            print(f"{left}{' ' * pad}{right}")
        else:
            print(left)
    print()
    print(fmt.border_bottom())
    print()


def _print_info_panel():
    print()
    print(fmt.separator_line("agent profile"))
    print()
    print(fmt.info_row("Agent Name", "RYZEN/Zen (AI Coding Agent)"))
    print(fmt.info_row("Owner", "Master Ken"))
    print(fmt.info_row("Engine", f"{state.PROVIDER['name'].upper()} API"))
    print(fmt.info_row("Model", state.MODEL_NAME))
    print(fmt.info_row("Features", "Memory, Files, Web Search, Git, Docs"))
    print()
    print(fmt.border_bottom())
    print()


def _print_medsos_panel():
    print()
    print(fmt.separator_line("social media"))
    print()
    print(fmt.info_row("GitHub", "https://github.com/RydzzKen"))
    print(fmt.info_row("Instagram", "https://instagram.com/satoru_Ian"))
    print(fmt.info_row("TikTok", "https://tiktok.com/@yxeel05"))
    print()
    print(fmt.border_bottom())
    print()


def _print_status_panel(contents):
    mem_count = 0
    try:
        mem_count = len(memory.load_memory_data())
    except Exception:
        mem_count = 0
    open_tasks = 0
    try:
        open_tasks = len(tasks.load_tasks().get("tasks", []))
    except Exception:
        open_tasks = 0

    print()
    print(fmt.separator_line("agent status"))
    print()
    print(fmt.info_row("Provider", state.PROVIDER['name']))
    print(fmt.info_row("Model", state.MODEL_NAME))
    print(fmt.info_row("API Key", provider.mask_api_key(provider.active_key())))
    endpoint = state.PROVIDER["openrouter_base_url"] + "/chat/completions" if state.PROVIDER["name"] == "openrouter" else state.BASE_URL.split('?')[0]
    print(fmt.info_row("Endpoint", endpoint))
    print(fmt.info_row("Workspace", state.WORKSPACE_DIR))
    print(fmt.info_row("Memori", f"{mem_count} fakta"))
    print(fmt.info_row("Tugas", f"{open_tasks} belum selesai"))
    print(fmt.info_row("Riwayat", f"{len(contents)} pesan"))
    think_str = f"{colors.C_SUCCESS}ON{colors.C_RESET}" if state.THINK_ENABLED else f"{colors.C_FG_DIM}OFF{colors.C_RESET}"
    print(f"{colors.C_YELLOW}{'Berpikir':<14}{colors.C_RESET} {think_str}")
    print()
    print(fmt.border_bottom())
    print()


def _print_usage_panel():
    print()
    print(fmt.separator_line("token usage"))
    print()
    print(fmt.info_row("Requests", str(usage.USAGE_STATS['requests'])))
    print(fmt.info_row("Prompt Token", str(usage.USAGE_STATS['prompt_tokens'])))
    print(fmt.info_row("Output Token", str(usage.USAGE_STATS['candidates_tokens'])))
    print(fmt.info_row("Total Token", str(usage.USAGE_STATS['total_tokens'])))
    print()
    print(fmt.border_bottom())
    print()


def _print_model_panel():
    print()
    print(fmt.separator_line(f"provider: {state.PROVIDER['name'].upper()}"))
    print()
    print(f"{fmt.BORDER_V} {colors.C_FG_DIM}Ganti provider dulu dengan{colors.C_RESET} {colors.C_BOLD}/connect{colors.C_RESET}")

    if state.PROVIDER["name"] == "openrouter":
        model_list = client.fetch_openrouter_models() or state.OR_MODELS
        if not model_list:
            print(f"{fmt.BORDER_V} {colors.C_ERROR}Gagal mengambil daftar model dari OpenRouter.{colors.C_RESET}")
        else:
            free = [m for m in model_list if m.endswith(":free")]
            paid = [m for m in model_list if not m.endswith(":free")]
            ordered = free + paid
            state.LAST_MODEL_LIST = ordered
            print(f"{fmt.BORDER_V} {colors.C_BOLD}{colors.C_SUCCESS}MODEL ({len(model_list)} tersedia, {len(free)} gratis){colors.C_RESET}")
            shown = ordered[:30]
            for i, m in enumerate(shown, 1):
                tag = f" {colors.C_SUCCESS}FREE{colors.C_RESET}" if m.endswith(":free") else ""
                marker = f"{colors.C_SUCCESS}●{colors.C_RESET}" if m == state.MODEL_NAME else f"{colors.C_FG_DIM}○{colors.C_RESET}"
                print(f" {marker} {colors.C_BOLD}{i:>2}.{colors.C_RESET} {m}{tag}")
            if len(ordered) > 30:
                print(f"{fmt.BORDER_V} {colors.C_FG_DIM}...dan {len(ordered) - 30} model lain{colors.C_RESET}")
    else:
        state.LAST_MODEL_LIST = models.AVAILABLE_MODELS
        print(f"{fmt.BORDER_V} {colors.C_BOLD}{colors.C_SUCCESS}MODEL GEMINI{colors.C_RESET}")
        for i, m in enumerate(models.AVAILABLE_MODELS, 1):
            marker = f"{colors.C_SUCCESS}●{colors.C_RESET}" if m == state.MODEL_NAME else f"{colors.C_FG_DIM}○{colors.C_RESET}"
            print(f" {marker} {colors.C_BOLD}{i:>2}.{colors.C_RESET} {m}")

    print(f"{fmt.BORDER_V} {colors.C_FG_DIM}Ketik{colors.C_RESET} {colors.C_BOLD}/model <nomor>{colors.C_RESET} {colors.C_FG_DIM}atau{colors.C_RESET} {colors.C_BOLD}/model <id>{colors.C_RESET}")
    print()
    print(fmt.border_bottom())


def _handle_model_switch(arg):
    if arg.lower() in ("gemini", "openrouter"):
        target = arg.lower()
        have_key = state.PROVIDER["gemini_api_key"] if target == "gemini" else state.PROVIDER["openrouter_api_key"]
        if not have_key:
            print(f"{fmt.BORDER_V} {colors.C_ERROR}Belum ada API key {target}. Pakai{colors.C_RESET} {colors.C_BOLD}/connect {target} <key>{colors.C_RESET}\n")
        else:
            provider.set_provider(target)
            print(f"{fmt.BORDER_V} {colors.C_SUCCESS}Provider diubah ke: {colors.C_BOLD}{state.PROVIDER['name']}{colors.C_RESET}")
            print(f"{fmt.BORDER_V} {colors.C_FG_DIM}Ketik{colors.C_RESET} {colors.C_BOLD}/model{colors.C_RESET} {colors.C_FG_DIM}untuk melihat daftar model.{colors.C_RESET}\n")
        return

    if arg.lower() == "free" and state.PROVIDER["name"] == "openrouter":
        model_list = client.fetch_openrouter_models() or state.OR_MODELS
        free = [m for m in model_list if m.endswith(":free")]
        if not free:
            print(f"{fmt.BORDER_V} {colors.C_ERROR}Tidak ada model gratis yang terambil.{colors.C_RESET}\n")
            return
        state.LAST_MODEL_LIST = free
        print()
        print(fmt.separator_line(f"model gratis ({len(free)})"))
        for i, m in enumerate(free[:30], 1):
            marker = f"{colors.C_SUCCESS}●{colors.C_RESET}" if m == state.MODEL_NAME else f"{colors.C_FG_DIM}○{colors.C_RESET}"
            print(f" {marker} {colors.C_BOLD}{i:>2}.{colors.C_RESET} {m}")
        if len(free) > 30:
            print(f"{fmt.BORDER_V} {colors.C_FG_DIM}...dan {len(free) - 30} model gratis lain{colors.C_RESET}")
        print()
        print(fmt.border_bottom())
        print()
        return

    chosen = None
    if arg.isdigit():
        idx = int(arg) - 1
        if 0 <= idx < len(state.LAST_MODEL_LIST):
            chosen = state.LAST_MODEL_LIST[idx]
    elif arg in state.LAST_MODEL_LIST:
        chosen = arg
    elif arg:
        chosen = arg
    if chosen:
        models.set_model(chosen)
        print(f"{fmt.BORDER_V} {colors.C_SUCCESS}Model diubah ke: {colors.C_BOLD}{state.MODEL_NAME}{colors.C_RESET}\n")
    else:
        print(f"{fmt.BORDER_V} {colors.C_ERROR}Model '{arg}' tidak valid. Ketik /model untuk daftar.{colors.C_RESET}\n")


def _handle_connect(user_input):
    parts_conn = user_input.split(None, 2)
    if len(parts_conn) >= 2 and parts_conn[1].lower() in ("gemini", "openrouter"):
        pname = parts_conn[1].lower()
        pkey = parts_conn[2].strip() if len(parts_conn) >= 3 else ""
        if pkey:
            base = "" if pname == "gemini" else "https://openrouter.ai/api/v1"
            provider.set_key(pname, pkey, base)
        else:
            stored = state.PROVIDER["gemini_api_key"] if pname == "gemini" else state.PROVIDER["openrouter_api_key"]
            if not stored:
                print(f"{fmt.BORDER_V} {colors.C_ERROR}Belum ada API key {pname} tersimpan. Pakai{colors.C_RESET} {colors.C_BOLD}/connect {pname} <key>{colors.C_RESET}\n")
                return
            provider.set_provider(pname)
        print(f"{fmt.BORDER_V} {colors.C_SUCCESS}Terhubung ke provider: {colors.C_BOLD}{state.PROVIDER['name']}{colors.C_RESET}")
        print(f"{fmt.BORDER_V} {colors.C_FG_DIM}API key auto-save ke .env (sudah di .gitignore){colors.C_RESET}")
        print(f"{fmt.BORDER_V} {colors.C_FG_DIM}Ketik{colors.C_RESET} {colors.C_BOLD}/model{colors.C_RESET} {colors.C_FG_DIM}untuk melihat daftar model.{colors.C_RESET}\n")
    else:
        prov = prompt.get_input(f"{fmt.BORDER_V} {colors.C_BOLD}Provider (gemini/openrouter){colors.C_RESET} > ").strip().lower()
        if prov not in ("gemini", "openrouter"):
            print(f"{fmt.BORDER_V} {colors.C_ERROR}Provider tidak dikenal: {prov}{colors.C_RESET}\n")
            return
        stored = state.PROVIDER["gemini_api_key"] if prov == "gemini" else state.PROVIDER["openrouter_api_key"]
        prompt_txt = f"{fmt.BORDER_V} {colors.C_BOLD}API Key (kosongkan jika sdh tersimpan){colors.C_RESET} > " if stored else f"{fmt.BORDER_V} {colors.C_BOLD}API Key{colors.C_RESET} > "
        key = prompt.get_input(prompt_txt).strip()
        if not key:
            if not stored:
                print(f"{fmt.BORDER_V} {colors.C_ERROR}API key kosong.{colors.C_RESET}\n")
                return
            key = stored
        base = ""
        if prov == "openrouter":
            base = prompt.get_input(f"{fmt.BORDER_V} {colors.C_BOLD}Base URL (kosongkan untuk default){colors.C_RESET} > ").strip()
        provider.set_key(prov, key, base)
        print(f"{fmt.BORDER_V} {colors.C_SUCCESS}Terhubung ke provider: {colors.C_BOLD}{state.PROVIDER['name']}{colors.C_RESET}\n")
        print(f"{fmt.BORDER_V} {colors.C_FG_DIM}Ketik{colors.C_RESET} {colors.C_BOLD}/model{colors.C_RESET} {colors.C_FG_DIM}untuk menarik daftar model.{colors.C_RESET}\n")


def _handle_think(user_input):
    arg = user_input[6:].strip().lower()
    if arg == "on":
        state.THINK_ENABLED = True
    elif arg == "off":
        state.THINK_ENABLED = False
    else:
        state.THINK_ENABLED = not state.THINK_ENABLED
    state_str = f"{colors.C_SUCCESS}ON{colors.C_RESET}" if state.THINK_ENABLED else f"{colors.C_ERROR}OFF{colors.C_RESET}"
    hint = ""
    if state.THINK_ENABLED:
        if state.PROVIDER["name"] == "gemini" and state.MODEL_NAME.startswith("gemini-2.5"):
            hint = f" {colors.C_FG_DIM}(native thinking Gemini 2.5){colors.C_RESET}"
        elif state.PROVIDER["name"] == "openrouter":
            hint = f" {colors.C_FG_DIM}(reasoning ditangkap bila model support){colors.C_RESET}"
        else:
            hint = f" {colors.C_FG_DIM}(CoT fallback via prompt){colors.C_RESET}"
    print(f"{fmt.BORDER_V} {colors.C_THINK_FG}Berpikir: {state_str}{hint}{colors.C_RESET}\n")


def models_placeholder_get_project_info():
    from tools import project
    return project.get_project_info()


if __name__ == "__main__":
    main()
