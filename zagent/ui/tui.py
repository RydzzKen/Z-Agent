"""Z-Agent TUI — Textual-based Terminal User Interface."""
import asyncio

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Footer, Header, Input, Label, Static
from textual.widgets._option_list import Option

from . import colors
from . import clipboard as clip
from . import widgets as w
from .modals import ModelPanelScreen, ConnectPanelScreen, SessionPanelScreen
from ..config import state
from ..config import provider
from ..config import models
from ..llm import client
from ..llm import usage
from ..tools import registry
from ..tools import prompt as prompt_mod
from ..tools import memory
from ..tools import tasks
from ..tools import project
from ..tools import sessions


# Command list for autocomplete
COMMANDS_LIST = [
    ("/status",    "Status agent & koneksi"),
    ("/model",     "Ganti model AI"),
    ("/connect",   "Hubungkan provider & API key"),
    ("/think",     "Mode berpikir ON/OFF"),
    ("/session",   "Kelola sesi percakapan"),
    ("/tasks",     "Lihat daftar tugas"),
    ("/project",   "Info project saat ini"),
    ("/usage",     "Ringkasan pemakaian token"),
    ("/info",      "Profil agent"),
    ("/medsos",    "Media sosial developer"),
    ("/new",       "Mulai sesi baru"),
    ("/reset",     "Reset riwayat percakapan"),
    ("/clear",     "Bersihkan layar"),
]


class ZAgentTUI(App):
    """Z-Agent Terminal User Interface built with Textual."""

    TITLE = "Z-Agent"
    SUB_TITLE = "AI Coding Agent"

    CSS_PATH = "tui_styles.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+r", "reset_chat", "Reset"),
        Binding("ctrl+s", "show_status", "Status"),
        Binding("ctrl+t", "toggle_think", "Toggle Think"),
        Binding("ctrl+y", "copy_last", "Copy last message", show=False),
        Binding("slash", "focus_input", "Command", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.contents = []
        self.is_processing = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="main-container"):
            with ScrollableContainer(id="chat-area"):
                yield from self._build_welcome()

            with Vertical(id="sidebar"):
                yield w.StatusBar(
                    provider=state.PROVIDER["name"],
                    model=state.MODEL_NAME,
                )
                yield w.UsageWidget(
                    requests=usage.USAGE_STATS["requests"],
                    prompt_tokens=usage.USAGE_STATS["prompt_tokens"],
                    output_tokens=usage.USAGE_STATS["candidates_tokens"],
                    total_tokens=usage.USAGE_STATS["total_tokens"],
                )
                yield w.SessionInfo(
                    session_id=sessions.get_active_session() or "",
                    message_count=len(self.contents),
                )
                yield w.ThinkIndicator(enabled=state.THINK_ENABLED)
                yield w.CommandPalette()

        with Vertical(id="input-area"):
            yield w.CommandPopup(id="cmd-popup")
            with Horizontal(id="input-container"):
                yield Input(placeholder="Ketik pesan atau /command...", id="user-input")

        yield Footer()

    def _build_welcome(self):
        """Build initial welcome screen widgets."""
        widgets = []
        widgets.append(w.SeparatorLine("Z-Agent"))
        widgets.append(Label(""))
        widgets.append(Label("  ╔══════════════════════════════════════╗"))
        widgets.append(Label("  ║       Z - A G E N T   T U I          ║"))
        widgets.append(Label("  ║    AI Coding Agent · Terminal UI     ║"))
        widgets.append(Label("  ╚══════════════════════════════════════╝"))
        widgets.append(Label(""))
        model_str = f"{state.PROVIDER['name']}/{state.MODEL_NAME}"
        widgets.append(Label(f"  agent :  {state.MODEL_NAME}  ({model_str})"))
        widgets.append(Label(""))
        widgets.append(w.SeparatorLine("quick start"))
        widgets.append(Label(""))
        widgets.append(Label("  Ketik pesan di bawah untuk mulai chat"))
        widgets.append(Label("  Atau gunakan /command untuk perintah"))
        widgets.append(Label(""))
        widgets.append(Label("  Ctrl+Y  copy pesan terakhir"))
        widgets.append(Label("  Ctrl+V  paste (atau tombol paste terminal)"))
        widgets.append(Label("  Tab     autocomplete perintah /"))
        widgets.append(Label(""))
        widgets.append(w.SeparatorLine())
        return widgets

    def on_mount(self):
        """Focus input on mount. Always start fresh session."""
        provider.ensure_initialized()
        self.query_one("#user-input").focus()
        self.contents = []
        sessions.begin_new_session()
        self._update_session_info()

    def _load_session_messages(self, contents):
        """Load session contents into the chat area."""
        chat = self.query_one("#chat-area")
        # Clear existing widgets except the static ones we'll rebuild
        for child in list(chat.children):
            child.remove()

        for item in contents[-20:]:  # Show last 20 messages
            role = item.get("role")
            parts = item.get("parts", [])
            for p in parts:
                if "text" in p:
                    if role == "user":
                        chat.mount(w.UserMessage(p["text"]))
                    else:
                        chat.mount(w.AIMessage(p["text"]))
                elif "functionCall" in p:
                    fc = p["functionCall"]
                    is_read = fc["name"] in ("read_file", "list_directory", "search_in_code", "get_project_info")
                    chat.mount(w.ToolCallMessage(
                        fc["name"], fc.get("args", {}),
                        is_read=is_read,
                    ))
        self._update_session_info()
        self._scroll_chat_bottom()

    def _update_session_info(self):
        """Refresh sidebar session info."""
        try:
            si = self.query_one(w.SessionInfo)
            sid = sessions.get_active_session() or ""
            name = ""
            if sid:
                meta = sessions.get_meta(sid)
                name = sessions.session_name(meta) or sid
            si.session_id = name
            si.message_count = len(self.contents)
        except Exception:
            pass

    def _update_status(self):
        """Refresh sidebar status."""
        try:
            sb = self.query_one(w.StatusBar)
            sb.provider = state.PROVIDER["name"]
            sb.model = state.MODEL_NAME
        except Exception:
            pass

    def _update_think(self):
        """Refresh think indicator."""
        try:
            ti = self.query_one(w.ThinkIndicator)
            ti.enabled = state.THINK_ENABLED
        except Exception:
            pass

    def _update_usage(self):
        """Refresh sidebar usage widget."""
        try:
            uw = self.query_one(w.UsageWidget)
            uw.requests = usage.USAGE_STATS["requests"]
            uw.prompt_tokens = usage.USAGE_STATS["prompt_tokens"]
            uw.output_tokens = usage.USAGE_STATS["candidates_tokens"]
            uw.total_tokens = usage.USAGE_STATS["total_tokens"]
        except Exception:
            pass

    def _reset_usage(self):
        """Reset token usage counters and refresh the sidebar widget."""
        usage.USAGE_STATS.update({"requests": 0, "prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0})
        self._update_usage()

    def _scroll_chat_bottom(self):
        """Scroll chat area to bottom."""
        try:
            chat = self.query_one("#chat-area")
            chat.scroll_end(animate=False)
        except Exception:
            pass

    # ── Input handling ──────────────────────────────────────────────

    @property
    def clipboard(self) -> str:
        """Paste source: local Textual clipboard first, else system clipboard."""
        if self._clipboard:
            return self._clipboard
        return clip.read_system_clipboard()

    def copy_to_clipboard(self, text: str) -> None:
        """Copy to local/OSC52 clipboard, then push to the real system clipboard."""
        super().copy_to_clipboard(text)
        clip.copy_to_system_clipboard(text)

    async def on_input_changed(self, event: Input.Changed):
        """Show/hide autocomplete popup when typing /."""
        popup = self.query_one(w.CommandPopup)
        text = event.value

        if text.startswith("/") and text.strip() != "":
            popup.filter(text)
            if popup.has_matches():
                popup.add_class("visible")
            else:
                popup.remove_class("visible")
        else:
            popup.remove_class("visible")

    async def on_input_submitted(self, event: Input.Submitted):
        """Handle user input submission."""
        user_input = event.value.strip()
        if not user_input:
            return

        # Close popup if open
        popup = self.query_one(w.CommandPopup)
        popup.remove_class("visible")

        # Clear input immediately
        inp = self.query_one("#user-input")
        inp.value = ""
        inp.focus()

        if self.is_processing:
            return

        # Handle slash commands locally
        if await self._handle_slash_command(user_input):
            return

        # Process with AI
        await self._process_ai_message(user_input)

    async def on_key(self, event):
        """Handle key events for popup navigation."""
        popup = self.query_one(w.CommandPopup)
        if not popup.has_class("visible"):
            return

        ol = popup.query_one("#cmd-list")
        if event.key == "down":
            event.prevent_default()
            if ol.option_count > 0:
                idx = (ol.highlighted or 0) + 1
                if idx < ol.option_count:
                    ol.highlighted = idx
        elif event.key == "up":
            event.prevent_default()
            if ol.option_count > 0:
                idx = (ol.highlighted or 0) - 1
                if idx >= 0:
                    ol.highlighted = idx
        elif event.key == "escape":
            event.prevent_default()
            popup.remove_class("visible")
            self.query_one("#user-input").focus()
        elif event.key == "tab":
            selected = popup.get_selected()
            if selected:
                event.prevent_default()
                popup.remove_class("visible")
                inp = self.query_one("#user-input")
                inp.value = selected
                inp.cursor_position = len(selected)
                inp.focus()
        elif event.key == "enter":
            selected = popup.get_selected()
            if selected:
                event.prevent_default()
                popup.remove_class("visible")
                inp = self.query_one("#user-input")
                inp.value = selected
                inp.cursor_position = len(selected)
                inp.focus()

    async def _handle_slash_command(self, user_input: str) -> bool:
        """Handle slash commands. Returns True if handled locally."""
        chat = self.query_one("#chat-area")
        cmd = user_input.lower().strip()

        if cmd in ("exit", "quit"):
            self.exit()
            return True

        if cmd == "/":
            chat.mount(w.SeparatorLine("commands"))
            for c, d in w.CommandPalette.COMMANDS:
                chat.mount(Label(f"  {c:<10} {d}"))
            chat.mount(w.SeparatorLine())
            self._scroll_chat_bottom()
            return True

        if cmd == "/clear":
            for child in list(chat.children):
                child.remove()
            for widget in self._build_welcome():
                chat.mount(widget)
            self._scroll_chat_bottom()
            return True

        if cmd == "/status":
            await self._show_status_panel()
            return True

        if cmd == "/usage":
            await self._show_usage_panel()
            return True

        if cmd == "/info":
            await self._show_info_panel()
            return True

        if cmd == "/project":
            result = await asyncio.to_thread(project.get_project_info)
            chat.mount(w.SeparatorLine("project info"))
            chat.mount(w.AIMessage(result))
            chat.mount(w.SeparatorLine())
            self._scroll_chat_bottom()
            return True

        if cmd == "/tasks":
            result = await asyncio.to_thread(tasks.list_tasks)
            chat.mount(w.SeparatorLine("tasks"))
            chat.mount(w.AIMessage(result))
            chat.mount(w.SeparatorLine())
            self._scroll_chat_bottom()
            return True

        if cmd == "/model":
            self._open_model_panel()
            return True

        if cmd.startswith("/model "):
            arg = user_input[7:].strip()
            await self._handle_model_switch(arg)
            return True

        if cmd == "/connect" or cmd.startswith("/connect"):
            if cmd == "/connect":
                self._open_connect_panel()
            else:
                await self._handle_connect(user_input)
            return True

        if cmd.startswith("/think"):
            arg = user_input[6:].strip().lower()
            if arg == "on":
                state.THINK_ENABLED = True
            elif arg == "off":
                state.THINK_ENABLED = False
            else:
                state.THINK_ENABLED = not state.THINK_ENABLED
            self._update_think()
            hint = ""
            if state.THINK_ENABLED:
                if state.PROVIDER["name"] == "gemini" and state.MODEL_NAME.startswith("gemini-2.5"):
                    hint = " (native thinking Gemini 2.5)"
                elif state.PROVIDER["name"] == "openrouter":
                    hint = " (reasoning captured if model supports)"
                else:
                    hint = " (CoT fallback via prompt)"
            chat.mount(w.SeparatorLine("thinking"))
            chat.mount(Label(f"  Thinking: {'ON' if state.THINK_ENABLED else 'OFF'}{hint}"))
            chat.mount(w.SeparatorLine())
            self._scroll_chat_bottom()
            return True

        if cmd in ("/reset",):
            self.contents = []
            for child in list(chat.children):
                child.remove()
            for widget in self._build_welcome():
                chat.mount(widget)
            self._update_session_info()
            self._scroll_chat_bottom()
            return True

        if cmd in ("/new",):
            self.contents = []
            self._reset_usage()
            sessions.begin_new_session()
            for child in list(chat.children):
                child.remove()
            for widget in self._build_welcome():
                chat.mount(widget)
            self._update_session_info()
            self._scroll_chat_bottom()
            return True

        if cmd.startswith("/session"):
            await self._handle_session(user_input)
            return True

        return False

    # ── AI processing ───────────────────────────────────────────────

    async def _process_ai_message(self, user_input: str):
        """Process user message through the AI agent loop."""
        chat = self.query_one("#chat-area")
        self.is_processing = True

        # Show user message
        chat.mount(w.UserMessage(user_input))
        self._scroll_chat_bottom()

        # Add to contents
        self.contents.append({"role": "user", "parts": [{"text": user_input}]})

        # Show loading
        loading = Label("  ⏳ Thinking...", id="loading-indicator")
        chat.mount(loading)
        self._scroll_chat_bottom()

        max_cycles = 10
        cycle_count = 0

        try:
            while cycle_count < max_cycles:
                cycle_count += 1

                # Run LLM call in thread to avoid blocking TUI
                model_content, err = await asyncio.to_thread(
                    client.generate_response,
                    self.contents,
                    prompt_mod.get_system_instruction_text(),
                    registry.gemini_tools,
                )

                if err is not None:
                    loading.remove()
                    chat.mount(w.AIMessage(f"Error: {err}"))
                    self.contents.pop()
                    break

                self.contents.append(model_content)
                parts = model_content.get("parts", [])
                function_called = False

                for part in parts:
                    if "functionCall" in part:
                        function_called = True
                        call_data = part["functionCall"]
                        fn_name = call_data["name"]
                        fn_args = call_data.get("args", {})

                        is_read = fn_name in ("read_file", "list_directory", "search_in_code", "get_project_info")

                        # Show tool call
                        chat.mount(w.ToolCallMessage(
                            fn_name, fn_args,
                            cycle=cycle_count, max_cycles=max_cycles,
                            is_read=is_read,
                        ))
                        self._scroll_chat_bottom()

                        # Execute tool in thread
                        result = await asyncio.to_thread(registry.execute_tool, fn_name, fn_args)

                        # Update the last tool call with result
                        tool_widgets = list(chat.query(w.ToolCallMessage))
                        if tool_widgets:
                            tool_widgets[-1]._result = str(result)
                            tool_widgets[-1].refresh()

                        self.contents.append({
                            "role": "user",
                            "parts": [{
                                "functionResponse": {
                                    "name": fn_name,
                                    "response": {"output": str(result)}
                                }
                            }]
                        })

                if function_called:
                    continue

                # Final response — remove loading indicator
                loading.remove()

                # Show thinking if enabled
                for part in parts:
                    if part.get("thought"):
                        if state.THINK_ENABLED:
                            chat.mount(w.ThinkingMessage(part.get("text", "")))
                    elif "text" in part:
                        chat.mount(w.AIMessage(part["text"]))

                chat.mount(w.SeparatorLine())
                self._scroll_chat_bottom()
                break

        except Exception as e:
            loading.remove()
            chat.mount(w.AIMessage(f"Error: {e}"))

        # Save session
        sid = sessions.get_active_session()
        if not sid or sessions.load_contents(sid) is None:
            sid = sessions.new_session_id()
        sessions.save_session(sid, self.contents)
        self._update_session_info()
        self._update_usage()
        self.is_processing = False

    # ── Panel handlers ──────────────────────────────────────────────

    async def _show_status_panel(self):
        chat = self.query_one("#chat-area")
        mem_count = 0
        try:
            mem_data = await asyncio.to_thread(memory.load_memory_data)
            mem_count = len(mem_data)
        except Exception:
            pass
        open_tasks = 0
        try:
            tdata = await asyncio.to_thread(tasks.load_tasks)
            open_tasks = len(tdata.get("tasks", []))
        except Exception:
            pass

        chat.mount(w.SeparatorLine("agent status"))
        chat.mount(Label(f"  Provider:     {state.PROVIDER['name']}"))
        chat.mount(Label(f"  Model:        {state.MODEL_NAME}"))
        chat.mount(Label(f"  API Key:      {provider.mask_api_key(provider.active_key())}"))
        chat.mount(Label(f"  Workspace:    {state.WORKSPACE_DIR}"))
        chat.mount(Label(f"  Memory:       {mem_count} facts"))
        chat.mount(Label(f"  Tasks:        {open_tasks} pending"))
        chat.mount(Label(f"  History:      {len(self.contents)} messages"))
        think_str = "ON" if state.THINK_ENABLED else "OFF"
        chat.mount(Label(f"  Thinking:     {think_str}"))
        chat.mount(w.SeparatorLine())
        self._scroll_chat_bottom()

    async def _show_usage_panel(self):
        chat = self.query_one("#chat-area")
        chat.mount(w.SeparatorLine("token usage"))
        chat.mount(Label(f"  Requests:     {usage.USAGE_STATS['requests']}"))
        chat.mount(Label(f"  Prompt:       {usage.USAGE_STATS['prompt_tokens']}"))
        chat.mount(Label(f"  Output:       {usage.USAGE_STATS['candidates_tokens']}"))
        chat.mount(Label(f"  Total:        {usage.USAGE_STATS['total_tokens']}"))
        chat.mount(w.SeparatorLine())
        self._scroll_chat_bottom()

    async def _show_info_panel(self):
        chat = self.query_one("#chat-area")
        chat.mount(w.SeparatorLine("agent profile"))
        chat.mount(Label(f"  Agent Name:   RYZEN/Zen (AI Coding Agent)"))
        chat.mount(Label(f"  Owner:        Master Ken"))
        chat.mount(Label(f"  Engine:       {state.PROVIDER['name'].upper()} API"))
        chat.mount(Label(f"  Model:        {state.MODEL_NAME}"))
        chat.mount(Label(f"  Features:     Memory, Files, Web, Git, Tasks"))
        chat.mount(w.SeparatorLine())
        self._scroll_chat_bottom()

    def _open_model_panel(self):
        """Open the model picker modal screen."""
        def on_select(model_id):
            asyncio.create_task(self._apply_model_selection(model_id))

        self.push_screen(ModelPanelScreen(on_select=on_select))

    async def _apply_model_selection(self, model_id):
        """Apply model selection from modal."""
        chat = self.query_one("#chat-area")
        await asyncio.to_thread(models.set_model, model_id)
        self._update_status()
        chat.mount(Label(f"  Model changed to: {state.MODEL_NAME}"))
        chat.mount(w.SeparatorLine())
        self._scroll_chat_bottom()

    def _open_connect_panel(self):
        """Open the connect provider modal screen."""
        def on_connect(provider_name):
            self._update_status()
            chat = self.query_one("#chat-area")
            chat.mount(Label(f"  Connected to: {state.PROVIDER['name']}"))
            chat.mount(Label(f"  Use /model to see available models."))
            chat.mount(w.SeparatorLine())
            self._scroll_chat_bottom()

        self.push_screen(ConnectPanelScreen(on_connect=on_connect))

    async def _show_model_panel(self):
        chat = self.query_one("#chat-area")
        chat.mount(w.SeparatorLine(f"provider: {state.PROVIDER['name'].upper()}"))

        if state.PROVIDER["name"] == "openrouter":
            model_list = await asyncio.to_thread(client.fetch_openrouter_models) or state.OR_MODELS
            if not model_list:
                chat.mount(Label("  Failed to fetch OpenRouter models."))
            else:
                free = [m for m in model_list if m.endswith(":free")]
                paid = [m for m in model_list if not m.endswith(":free")]
                ordered = free + paid
                state.LAST_MODEL_LIST = ordered
                chat.mount(Label(f"  Models: {len(model_list)} available, {len(free)} free"))
                for i, m in enumerate(ordered[:30], 1):
                    tag = " [FREE]" if m.endswith(":free") else ""
                    marker = "*" if m == state.MODEL_NAME else " "
                    chat.mount(Label(f"  {marker} {i:>2}. {m}{tag}"))
        else:
            state.LAST_MODEL_LIST = models.AVAILABLE_MODELS
            chat.mount(Label("  GEMINI MODELS:"))
            for i, m in enumerate(models.AVAILABLE_MODELS, 1):
                marker = "*" if m == state.MODEL_NAME else " "
                chat.mount(Label(f"  {marker} {i:>2}. {m}"))

        chat.mount(Label("  Use /model <number> or /model <id> to switch"))
        chat.mount(w.SeparatorLine())
        self._scroll_chat_bottom()

    async def _handle_model_switch(self, arg):
        chat = self.query_one("#chat-area")

        if arg.lower() in ("gemini", "openrouter"):
            target = arg.lower()
            have_key = state.PROVIDER["gemini_api_key"] if target == "gemini" else state.PROVIDER["openrouter_api_key"]
            if not have_key:
                chat.mount(Label(f"  No API key for {target}. Use /connect {target} <key>"))
            else:
                await asyncio.to_thread(provider.set_provider, target)
                self._update_status()
                chat.mount(Label(f"  Provider changed to: {state.PROVIDER['name']}"))
            self._scroll_chat_bottom()
            return

        if arg.lower() == "free" and state.PROVIDER["name"] == "openrouter":
            model_list = await asyncio.to_thread(client.fetch_openrouter_models) or state.OR_MODELS
            free = [m for m in model_list if m.endswith(":free")]
            state.LAST_MODEL_LIST = free
            chat.mount(w.SeparatorLine(f"free models ({len(free)})"))
            for i, m in enumerate(free[:30], 1):
                marker = "*" if m == state.MODEL_NAME else " "
                chat.mount(Label(f"  {marker} {i:>2}. {m}"))
            chat.mount(w.SeparatorLine())
            self._scroll_chat_bottom()
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
            await asyncio.to_thread(models.set_model, chosen)
            self._update_status()
            chat.mount(Label(f"  Model changed to: {state.MODEL_NAME}"))
        else:
            chat.mount(Label(f"  Invalid model: {arg}. Use /model to see list."))
        chat.mount(w.SeparatorLine())
        self._scroll_chat_bottom()

    async def _handle_connect(self, user_input):
        chat = self.query_one("#chat-area")
        parts = user_input.split(None, 2)
        if len(parts) >= 2 and parts[1].lower() in ("gemini", "openrouter"):
            pname = parts[1].lower()
            pkey = parts[2].strip() if len(parts) >= 3 else ""
            if pkey:
                base = "" if pname == "gemini" else "https://openrouter.ai/api/v1"
                await asyncio.to_thread(provider.set_key, pname, pkey, base)
            else:
                stored = state.PROVIDER["gemini_api_key"] if pname == "gemini" else state.PROVIDER["openrouter_api_key"]
                if not stored:
                    chat.mount(Label(f"  No stored key for {pname}. Use /connect {pname} <key>"))
                    self._scroll_chat_bottom()
                    return
                await asyncio.to_thread(provider.set_provider, pname)
            self._update_status()
            chat.mount(Label(f"  Connected to: {state.PROVIDER['name']}"))
            chat.mount(Label(f"  Use /model to see available models."))
        else:
            chat.mount(Label("  Usage: /connect <gemini|openrouter> <api_key>"))
        chat.mount(w.SeparatorLine())
        self._scroll_chat_bottom()

    async def _handle_session(self, user_input):
        chat = self.query_one("#chat-area")
        action = user_input[len("/session"):].strip()

        if not action:
            if not sessions.list_sessions():
                chat.mount(Label("  No saved sessions. Use /session baru"))
                chat.mount(w.SeparatorLine())
                self._scroll_chat_bottom()
                return
            def on_select(sid):
                asyncio.create_task(self._apply_session(sid))
            self.push_screen(SessionPanelScreen(on_select=on_select))
            return

        if action.lower() in ("baru", "new", "bersih", "clear"):
            self.contents = []
            self._reset_usage()
            sessions.begin_new_session()
            self._update_session_info()
            chat.mount(Label("  New session started."))
            self._scroll_chat_bottom()
            return

        if action.lower().startswith(("hapus", "delete", "del", "rm")):
            parts = action.split(None, 1)
            if len(parts) < 2:
                chat.mount(Label("  Usage: /session hapus <id|nama>  |  /session hapus semua"))
            else:
                target = parts[1].strip()
                if target.lower() in ("semua", "all", "semua-sesi"):
                    await asyncio.to_thread(sessions.delete_all_sessions)
                    self.contents = []
                    self._update_session_info()
                    chat.mount(Label("  Semua sesi dihapus."))
                else:
                    ids = await asyncio.to_thread(sessions.find_sessions, target)
                    if not ids:
                        chat.mount(Label(f"  Session '{target}' tidak ditemukan."))
                    else:
                        for sid in ids:
                            await asyncio.to_thread(sessions.delete_session, sid)
                            if sid == sessions.get_active_session():
                                self.contents = []
                        chat.mount(Label(f"  {len(ids)} sesi dihapus ({', '.join(ids)})."))
            self._scroll_chat_bottom()
            return

        # Load session by ID
        loaded = await asyncio.to_thread(sessions.load_contents, action)
        if loaded is None:
            chat.mount(Label(f"  Session '{action}' not found. Use /session to list."))
        else:
            self.contents = loaded
            self._reset_usage()
            for child in list(chat.children):
                child.remove()
            self._load_session_messages(loaded)
        chat.mount(w.SeparatorLine())
        self._scroll_chat_bottom()

    async def _apply_session(self, sid):
        """Muat sesi hasil pilihan panel interaktif /session."""
        chat = self.query_one("#chat-area")

        if sid == "__new__" or sid is None:
            self.contents = []
            self._reset_usage()
            sessions.begin_new_session()
            for child in list(chat.children):
                child.remove()
            for widget in self._build_welcome():
                chat.mount(widget)
            self._update_session_info()
            self._scroll_chat_bottom()
            return

        loaded = await asyncio.to_thread(sessions.load_contents, sid)
        if loaded is None:
            chat.mount(Label(f"  Session '{sid}' not found."))
        else:
            self.contents = loaded
            self._reset_usage()
            for child in list(chat.children):
                child.remove()
            sessions.save_session(sid, loaded)
            self._load_session_messages(loaded)
            self._update_session_info()
            self._scroll_chat_bottom()

    # ── Action handlers ─────────────────────────────────────────────

    def action_new_session(self):
        """Start a new session."""
        self.contents = []
        self._reset_usage()
        sessions.begin_new_session()
        chat = self.query_one("#chat-area")
        for child in list(chat.children):
            child.remove()
        for widget in self._build_welcome():
            chat.mount(widget)
        self._update_session_info()

    def action_reset_chat(self):
        """Reset chat history."""
        self.contents = []
        chat = self.query_one("#chat-area")
        for child in list(chat.children):
            child.remove()
        for widget in self._build_welcome():
            chat.mount(widget)
        self._update_session_info()

    def action_show_status(self):
        """Show status panel."""
        asyncio.create_task(self._show_status_panel())

    def action_toggle_think(self):
        """Toggle thinking mode."""
        state.THINK_ENABLED = not state.THINK_ENABLED
        self._update_think()

    def action_focus_input(self):
        """Focus the input field."""
        self.query_one("#user-input").focus()

    def action_copy_last(self):
        """Copy the most recent message (AI or user) to the clipboard."""
        chat = self.query_one("#chat-area")
        for child in reversed(list(chat.children)):
            if isinstance(child, (w.AIMessage, w.UserMessage)):
                text = getattr(child, "_text", "")
                if text:
                    self.copy_to_clipboard(text)
                    if clip.is_clipboard_supported():
                        self.notify("Copied to clipboard", timeout=2)
                    else:
                        self.notify("Tidak ada tool clipboard (install xclip/xsel)", timeout=4)
                else:
                    self.notify("No text to copy", timeout=2)
                return
        self.notify("No message to copy", timeout=2)


def run_tui():
    """Entry point to launch the TUI."""
    app = ZAgentTUI()
    app.run()
