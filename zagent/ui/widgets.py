"""Custom Textual widgets for Z-Agent TUI."""
from rich.markup import escape
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static, OptionList
from textual.widgets._option_list import Option


# ── Chat message widgets ─────────────────────────────────────────────


class UserMessage(Widget):
    """A user chat message bubble."""

    DEFAULT_CSS = """
    UserMessage {
        height: auto;
        max-height: 30;
        background: #262222;
        border-left: tall #30d158;
        padding: 1 1;
        margin: 0 0 1 0;
    }
    UserMessage Label {
        width: 100%;
        height: auto;
        padding: 0 1;
        color: #30d158;
        text-style: bold;
    }
    """

    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self._text = text

    def compose(self) -> ComposeResult:
        yield Label(f"You  {escape(self._text)}")


class AIMessage(Widget):
    """An AI response message bubble."""

    DEFAULT_CSS = """
    AIMessage {
        height: auto;
        max-height: 80;
        background: #262222;
        border-left: tall #ff9f0a;
        padding: 1 1;
        margin: 0 0 1 0;
    }
    AIMessage Label {
        width: 100%;
        height: auto;
        padding: 0 1;
        color: #fdfcfc;
    }
    """

    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self._text = text

    def compose(self) -> ComposeResult:
        for line in self._text.split("\n"):
            if line.strip():
                yield Label(escape(line))
            else:
                yield Label("")


class ThinkingMessage(Widget):
    """AI thinking/reasoning output."""

    DEFAULT_CSS = """
    ThinkingMessage {
        height: auto;
        max-height: 20;
        background: #262222;
        border-left: tall #ffd60a;
        padding: 1 1;
        margin: 0 0 1 0;
    }
    ThinkingMessage Label {
        width: 100%;
        height: auto;
        padding: 0 1;
        color: #ffd60a;
        text-style: dim;
    }
    """

    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self._text = text

    def compose(self) -> ComposeResult:
        for line in self._text.split("\n"):
            if line.strip():
                yield Label(escape(line))


class ToolCallMessage(Widget):
    """Tool call result display."""

    DEFAULT_CSS = """
    ToolCallMessage {
        height: auto;
        background: #242020;
        border-left: tall #9a9898;
        padding: 1 1;
        margin: 0 0 1 0;
    }
    ToolCallMessage .tool-name {
        width: 100%;
        height: auto;
        padding: 0 1;
        color: #ff9f0a;
        text-style: bold;
    }
    ToolCallMessage .tool-result {
        width: 100%;
        height: auto;
        padding: 0 1;
        color: #9a9898;
        text-style: dim;
    }
    """

    def __init__(self, tool_name: str, args: dict, result: str = "", cycle: int = 0, max_cycles: int = 10, is_read: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._tool_name = tool_name
        self._args = args
        self._result = result
        self._cycle = cycle
        self._max_cycles = max_cycles
        self._is_read = is_read

    def compose(self) -> ComposeResult:
        arrow = "→" if self._is_read else "←"
        args_str = self._format_args(self._args)
        cycle_tag = f" ({self._cycle}/{self._max_cycles})" if self._cycle else ""
        yield Label(f"{arrow} {self._tool_name}{args_str}{cycle_tag}", classes="tool-name")
        if self._result:
            s = str(self._result).replace("\n", " ").strip()
            if len(s) > 140:
                s = s[:140] + "..."
            yield Label(f"  {s}", classes="tool-result")

    def _format_args(self, args):
        if not args:
            return ""
        parts = []
        for k, v in args.items():
            val = repr(v) if isinstance(v, str) else str(v)
            if len(val) > 40:
                val = val[:37] + "..."
            parts.append(f"{k}={val}")
        return f"({', '.join(parts)})"


class SeparatorLine(Widget):
    """A horizontal separator line — sized to the available width."""

    DEFAULT_CSS = """
    SeparatorLine {
        height: 1;
        padding: 0;
        margin: 0;
    }
    """

    def __init__(self, label: str = "", **kwargs):
        super().__init__(**kwargs)
        self._label = label

    def render(self) -> Text:
        width = max(10, self.size.width)
        if self._label:
            prefix = f"─── {self._label} "
            return Text(prefix + "─" * max(0, width - len(prefix)), style="#3c3838")
        return Text("─" * width, style="#3c3838")


# ── Status sidebar widgets ────────────────────────────────────────────


class StatusBar(Widget):
    """Sidebar status display — updates live."""

    DEFAULT_CSS = """
    StatusBar {
        height: auto;
        padding: 1;
        background: #1e1a1a;
        border-left: tall #3c3838;
    }
    """

    provider = reactive("")
    model = reactive("")

    def __init__(self, provider: str = "", model: str = "", **kwargs):
        super().__init__(**kwargs)
        self.provider = provider
        self.model = model

    def render(self) -> Text:
        text = Text(style="#9a9898")
        text.append("┌─ Status ─┐", style="bold #ff9f0a")
        text.append("\n")
        text.append(f" Provider: {self.provider}")
        text.append("\n")
        text.append(f" Model: {self.model}")
        return text


class CommandPalette(Widget):
    """Sidebar command list."""

    DEFAULT_CSS = """
    CommandPalette {
        height: auto;
        padding: 1;
        background: #1e1a1a;
        border-left: tall #3c3838;
    }
    CommandPalette Label {
        width: 100%;
        height: auto;
        padding: 0 0;
    }
    """

    COMMANDS = [
        ("/status", "Status & info"),
        ("/model", "Ganti model"),
        ("/connect", "Setup API key"),
        ("/think", "Toggle berpikir"),
        ("/session", "Kelola sesi"),
        ("/tasks", "Daftar tugas"),
        ("/usage", "Token usage"),
        ("/info", "Profil agent"),
        ("/new", "Sesi baru"),
        ("/reset", "Reset riwayat"),
    ]

    def compose(self) -> ComposeResult:
        yield Label("┌─ Commands ─┐", classes="cmd-title")
        for cmd, desc in self.COMMANDS:
            yield Label(f" {cmd:<10} {desc}", classes="cmd-item")


class SessionInfo(Widget):
    """Sidebar session information — updates live."""

    DEFAULT_CSS = """
    SessionInfo {
        height: auto;
        padding: 1;
        background: #1e1a1a;
        border-left: tall #3c3838;
    }
    """

    session_id = reactive("")
    message_count = reactive(0)

    def __init__(self, session_id: str = "", message_count: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.session_id = session_id
        self.message_count = message_count

    def render(self) -> Text:
        sid_display = self.session_id if self.session_id else "(none)"
        text = Text(style="#9a9898")
        text.append("┌─ Session ─┐", style="bold #ff9f0a")
        text.append("\n")
        text.append(f" Name: {sid_display}")
        text.append("\n")
        text.append(f" Messages: {self.message_count}")
        return text


class ThinkIndicator(Widget):
    """Thinking mode ON/OFF indicator — updates live."""

    DEFAULT_CSS = """
    ThinkIndicator {
        height: auto;
        padding: 1;
        margin: 0;
    }
    """

    enabled = reactive(False)

    def __init__(self, enabled: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.enabled = enabled

    def render(self) -> Text:
        if self.enabled:
            return Text("Thinking: ON", style="bold #30d158")
        return Text("Thinking: OFF", style="#9a9898")


class UsageWidget(Widget):
    """Sidebar token usage display — updates live."""

    DEFAULT_CSS = """
    UsageWidget {
        height: auto;
        padding: 1;
        background: #1e1a1a;
        border-left: tall #3c3838;
    }
    """

    requests = reactive(0)
    prompt_tokens = reactive(0)
    output_tokens = reactive(0)
    total_tokens = reactive(0)

    def __init__(self, requests: int = 0, prompt_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.requests = requests
        self.prompt_tokens = prompt_tokens
        self.output_tokens = output_tokens
        self.total_tokens = total_tokens

    def render(self) -> Text:
        text = Text(style="#9a9898")
        text.append("┌─ Usage ─┐", style="bold #ff9f0a")
        text.append("\n")
        text.append(f" Reqs:    {self.requests}")
        text.append("\n")
        text.append(f" Prompt:  {self.prompt_tokens}")
        text.append("\n")
        text.append(f" Output:  {self.output_tokens}")
        text.append("\n")
        text.append(f" Total:   {self.total_tokens}")
        return text


class TokenBar(Widget):
    """One-line compact status bar shown under the input on narrow screens.

    Visible only when the terminal is too small for the sidebar (e.g. mobile /
    Termux). Shows a quick glance at token usage, model, and thinking mode.
    """

    DEFAULT_CSS = """
    TokenBar {
        height: 1;
        padding: 0 3;
        color: #9a9898;
        text-style: dim;
    }
    """

    requests = reactive(0)
    prompt_tokens = reactive(0)
    output_tokens = reactive(0)
    total_tokens = reactive(0)
    model = reactive("")
    thinking = reactive(False)

    def __init__(self, requests: int = 0, prompt_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0, model: str = "", thinking: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.requests = requests
        self.prompt_tokens = prompt_tokens
        self.output_tokens = output_tokens
        self.total_tokens = total_tokens
        self.model = model
        self.thinking = thinking

    def _short_total(self) -> str:
        n = self.total_tokens
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(n)

    def render(self) -> Text:
        parts = [f"⚡ {self.requests} req", f"{self._short_total()} tok"]
        if self.model:
            parts.append(self.model.split("/")[-1])
        parts.append("🧠 ON" if self.thinking else "🧠 OFF")
        return Text("  ·  ".join(parts), style="#9a9898")


# ── Autocomplete popup ──────────────────────────────────────────────


class CommandPopup(Widget):
    """Floating autocomplete popup for slash commands.

    Shows an OptionList that filters as the user types ``/``.
    """

    DEFAULT_CSS = """
    CommandPopup {
        height: auto;
        max-height: 14;
        width: 100%;
        background: #242020;
        border-top: solid #ff9f0a;
        padding: 0 0;
        display: none;
    }
    CommandPopup.visible {
        display: block;
    }
    CommandPopup OptionList {
        height: auto;
        max-height: 12;
        background: #242020;
        color: #fdfcfc;
        border: hidden;
    }
    CommandPopup OptionList > .option-list--option {
        color: #9a9898;
    }
    CommandPopup OptionList > .option-list--option-highlighted {
        color: #fdfcfc;
        background: #3c3838;
    }
    """

    COMMANDS = [
        ("/status", "Status agent & koneksi"),
        ("/model", "Ganti model AI"),
        ("/connect", "Hubungkan provider & API key"),
        ("/think", "Mode berpikir ON/OFF"),
        ("/session", "Kelola sesi percakapan"),
        ("/tasks", "Lihat daftar tugas"),
        ("/project", "Info project saat ini"),
        ("/usage", "Ringkasan pemakaian token"),
        ("/info", "Profil agent"),
        ("/medsos", "Media sosial developer"),
        ("/new", "Mulai sesi baru"),
        ("/reset", "Reset riwayat percakapan"),
        ("/clear", "Bersihkan layar"),
    ]

    def compose(self) -> ComposeResult:
        yield OptionList(id="cmd-list")

    def on_mount(self):
        self._populate(self.COMMANDS)

    def _populate(self, commands):
        ol = self.query_one("#cmd-list")
        ol.clear_options()
        for cmd, desc in commands:
            ol.add_option(Option(f"  {cmd:<12} {desc}", cmd))

    def filter(self, query: str):
        """Filter commands by query string (e.g. ``/mo``)."""
        q = query.lower().strip()
        if not q.startswith("/") or q == "/":
            matches = self.COMMANDS
        else:
            matches = [(c, d) for c, d in self.COMMANDS if c.startswith(q)]
        self._populate(matches)
        ol = self.query_one("#cmd-list")
        if ol.option_count > 0:
            ol.highlighted = 0

    def has_matches(self) -> bool:
        """Return True when the filtered option list is not empty."""
        ol = self.query_one("#cmd-list")
        return ol.option_count > 0

    def get_selected(self) -> str | None:
        """Return the command string of the highlighted option."""
        ol = self.query_one("#cmd-list")
        if ol.option_count == 0 or ol.highlighted is None:
            return None
        opt = ol.get_option_at_index(ol.highlighted)
        return opt.id if opt else None
