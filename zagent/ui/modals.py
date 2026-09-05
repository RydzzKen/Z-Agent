"""Modal screens for Z-Agent TUI — Model picker, Connect panel."""
import asyncio

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button, OptionList, Static
from textual.widgets._option_list import Option

from ..config import state
from ..config import provider
from ..config import models
from ..llm import client
from ..tools import sessions


class _SearchInput(Input):
    """Input that forwards up/down arrow keys to the list navigation."""

    def _on_key(self, event) -> None:
        if event.key in ("up", "down"):
            self.screen._move_highlight(1 if event.key == "down" else -1)
            event.stop()
            return
        super()._on_key(event)


# ── Model Picker Screen ──────────────────────────────────────────────


class ModelPanelScreen(ModalScreen):
    """Modal screen for picking AI model."""

    CSS = """
    ModelPanelScreen {
        align: center middle;
    }
    #model-dialog {
        width: 80;
        max-height: 35;
        height: auto;
        background: #1e1a1a;
        border: tall #ff9f0a;
        padding: 1 2;
    }
    #model-title {
        text-style: bold;
        color: #ff9f0a;
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    #model-subtitle {
        color: #9a9898;
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    #model-list {
        width: 1fr;
        height: auto;
        max-height: 22;
        background: #1e1a1a;
        color: #fdfcfc;
        border: hidden;
    }
    #model-list > .option-list--option {
        color: #9a9898;
    }
    #model-list > .option-list--option-highlighted {
        color: #fdfcfc;
        background: #3c3838;
    }
    #model-list > .option-list--option-disabled {
        color: #30d158;
        text-style: bold;
    }
    #model-input-row {
        height: 3;
        margin-top: 1;
        width: 1fr;
    }
    #model-search {
        width: 1fr;
        height: 3;
        background: #1e1a1a;
        color: #fdfcfc;
        border: tall #3c3838;
    }
    #model-search:focus {
        border: tall #ff9f0a;
    }
    #model-hint {
        color: #9a9898;
        height: 1;
        margin-top: 1;
    }
    #model-btn-row {
        height: 3;
        margin-top: 1;
        width: 1fr;
        align: center middle;
    }
    #model-btn-row Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select_model", "Select", show=False),
    ]

    def __init__(self, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self._on_select = on_select
        self._all_models = []
        self._filtered = []
        self._selected_idx = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="model-dialog"):
            yield Label("Model Selection", id="model-title")
            yield Label(f"Provider: {state.PROVIDER['name'].upper()}  |  Current: {state.MODEL_NAME}", id="model-subtitle")
            yield _SearchInput(placeholder="Search model...", id="model-search")
            yield OptionList(id="model-list")
            yield Label("↑/↓ navigate  |  Enter select  |  type to search  |  Esc cancel", id="model-hint")

    def on_mount(self):
        self._load_models()
        self.query_one("#model-search").focus()

    def _load_models(self):
        if state.PROVIDER["name"] == "openrouter":
            self._all_models = state.LAST_MODEL_LIST or state.OR_MODELS or []
        else:
            self._all_models = list(models.AVAILABLE_MODELS)

        self._filtered = list(self._all_models)
        self._render_list()

    def _render_list(self):
        ol = self.query_one("#model-list")
        prev_highlighted = None
        if ol.highlighted is not None and ol.option_count:
            prev_highlighted = ol.get_option_at_index(ol.highlighted).id
        ol.clear_options()
        current = state.MODEL_NAME

        for m in self._filtered:
            tag = " [FREE]" if m.endswith(":free") else ""
            is_current = m == current
            label = f"{'* ' if is_current else '  '}{m}{tag}"
            opt = Option(label, m)
            if is_current:
                opt.disabled = True
            ol.add_option(opt)

        if ol.option_count and prev_highlighted in self._filtered:
            ol.highlighted = self._filtered.index(prev_highlighted)
        elif ol.option_count:
            ol.highlighted = 0

    def _move_highlight(self, delta: int) -> None:
        ol = self.query_one("#model-list")
        if ol.option_count == 0:
            return
        idx = ol.highlighted
        if idx is None:
            idx = 0 if delta > 0 else ol.option_count - 1
        else:
            idx += delta
        if 0 <= idx < ol.option_count:
            ol.highlighted = idx

    async def on_input_changed(self, event: Input.Changed):
        query = event.value.lower().strip()
        if not query:
            self._filtered = list(self._all_models)
        else:
            self._filtered = [m for m in self._all_models if query in m.lower()]
        self._render_list()

    async def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        model_id = event.option_id
        if model_id and self._on_select:
            self._on_select(model_id)
        self.dismiss()

    def action_select_model(self):
        ol = self.query_one("#model-list")
        if ol.option_count > 0 and ol.highlighted is not None:
            opt = ol.get_option_at_index(ol.highlighted)
            model_id = opt.id
            if model_id and self._on_select:
                self._on_select(model_id)
            self.dismiss()

    def action_cancel(self):
        self.dismiss()


# ── Session Picker Screen ────────────────────────────────────────────


class SessionPanelScreen(ModalScreen):
    """Modal screen for picking / opening a session with ↑↓ + Enter."""

    CSS = """
    SessionPanelScreen {
        align: center middle;
    }
    #session-dialog {
        width: 74;
        max-height: 30;
        height: auto;
        background: #1e1a1a;
        border: tall #30d158;
        padding: 1 2;
    }
    #session-title {
        text-style: bold;
        color: #30d158;
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    #session-subtitle {
        color: #9a9898;
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    #session-list {
        width: 1fr;
        height: auto;
        max-height: 20;
        background: #1e1a1a;
        color: #fdfcfc;
        border: hidden;
    }
    #session-list > .option-list--option {
        color: #9a9898;
    }
    #session-list > .option-list--option-highlighted {
        color: #fdfcfc;
        background: #3c3838;
    }
    #session-hint {
        color: #9a9898;
        height: 1;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select_session", "Select", show=False),
        Binding("d", "delete_session", "Delete", show=False),
    ]

    def __init__(self, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self._on_select = on_select

    def compose(self) -> ComposeResult:
        with Vertical(id="session-dialog"):
            yield Label("Pilih Sesi", id="session-title")
            yield Label("↑/↓ pilih  |  Enter buka  |  d hapus  |  Esc batal", id="session-subtitle")
            yield OptionList(id="session-list")
            yield Label("↑/↓ navigate  |  Enter select  |  d delete  |  Esc cancel", id="session-hint")

    def on_mount(self):
        self._load_sessions()
        self.query_one("#session-list").focus()

    def _load_sessions(self):
        ol = self.query_one("#session-list")
        ol.clear_options()
        active = sessions.get_active_session()
        ordered = sessions.list_sessions()
        for sid, meta in ordered:
            name = sessions.session_name(meta) or sid
            n = len(meta.get("contents", []))
            marker = "●" if sid == active else "○"
            ol.add_option(Option(f"   {marker} {name}   ({n} pesan)", sid))
        ol.add_option(Option("   ＋ Buat sesi baru", "__new__"))
        if ol.option_count > 0:
            ol.highlighted = 0

    def _emit(self, sid):
        if sid and self._on_select:
            self._on_select(sid)
        self.dismiss()

    async def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        self._emit(event.option_id)

    def action_select_session(self):
        ol = self.query_one("#session-list")
        if ol.option_count > 0 and ol.highlighted is not None:
            opt = ol.get_option_at_index(ol.highlighted)
            self._emit(opt.id)

    def action_delete_session(self):
        ol = self.query_one("#session-list")
        if ol.option_count > 0 and ol.highlighted is not None:
            opt = ol.get_option_at_index(ol.highlighted)
            if opt.id == "__new__":
                return
            sessions.delete_session(opt.id)
            self._load_sessions()

    def action_cancel(self):
        self.dismiss()


# ── Connect Panel Screen ─────────────────────────────────────────────


class ConnectPanelScreen(ModalScreen):
    """Modal screen for connecting to a provider."""

    CSS = """
    ConnectPanelScreen {
        align: center middle;
    }
    #connect-dialog {
        width: 70;
        height: auto;
        background: #1e1a1a;
        border: tall #007aff;
        padding: 1 2;
    }
    #connect-title {
        text-style: bold;
        color: #007aff;
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    #connect-provider-label {
        color: #9a9898;
        height: 1;
    }
    #connect-provider-row {
        height: 3;
        width: 1fr;
        margin: 0 0 1 0;
    }
    #connect-gemini-btn {
        width: 1fr;
        height: 3;
        background: #1e1a1a;
        color: #fdfcfc;
        border: tall #3c3838;
    }
    #connect-openrouter-btn {
        width: 1fr;
        height: 3;
        background: #1e1a1a;
        color: #fdfcfc;
        border: tall #3c3838;
    }
    #connect-key-label {
        color: #9a9898;
        height: 1;
        margin-top: 1;
    }
    #connect-key-input {
        width: 1fr;
        height: 3;
        background: #1e1a1a;
        color: #fdfcfc;
        border: tall #3c3838;
    }
    #connect-key-input:focus {
        border: tall #007aff;
    }
    #connect-status {
        color: #9a9898;
        height: 1;
        margin-top: 1;
    }
    #connect-btn-row {
        height: 3;
        margin-top: 1;
        width: 1fr;
        align: center middle;
    }
    #connect-btn-row Button {
        margin: 0 1;
    }
    #connect-hint {
        color: #9a9898;
        height: 1;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+enter", "connect", "Connect", show=False),
    ]

    def __init__(self, on_connect=None, **kwargs):
        super().__init__(**kwargs)
        self._on_connect = on_connect
        self._selected_provider = "gemini"

    def compose(self) -> ComposeResult:
        with Vertical(id="connect-dialog"):
            yield Label("Connect Provider", id="connect-title")

            yield Label("Select provider:", id="connect-provider-label")
            with Horizontal(id="connect-provider-row"):
                yield Button("Gemini", id="connect-gemini-btn", variant="primary")
                yield Button("OpenRouter", id="connect-openrouter-btn", variant="default")

            yield Label("API Key:", id="connect-key-label")
            yield Input(placeholder="Enter your API key...", password=True, id="connect-key-input")

            stored = provider.mask_api_key(provider.active_key())
            yield Label(f"Current key: {stored}", id="connect-status")

            with Horizontal(id="connect-btn-row"):
                yield Button("Connect", id="connect-do", variant="primary")
                yield Button("Cancel", id="connect-cancel", variant="default")

            yield Label("Tab switch provider  |  Ctrl+Enter connect  |  Esc cancel", id="connect-hint")

    def on_mount(self):
        self.query_one("#connect-key-input").focus()
        # Highlight current provider button
        self._update_provider_ui()

    def _update_provider_ui(self):
        gemini_btn = self.query_one("#connect-gemini-btn")
        or_btn = self.query_one("#connect-openrouter-btn")
        if self._selected_provider == "gemini":
            gemini_btn.variant = "primary"
            or_btn.variant = "default"
        else:
            gemini_btn.variant = "default"
            or_btn.variant = "primary"

        key_input = self.query_one("#connect-key-input")
        if self._selected_provider == "gemini":
            key_input.placeholder = "Enter Gemini API key..."
        else:
            key_input.placeholder = "Enter OpenRouter API key..."

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "connect-gemini-btn":
            self._selected_provider = "gemini"
            self._update_provider_ui()
            self.query_one("#connect-key-input").focus()
        elif event.button.id == "connect-openrouter-btn":
            self._selected_provider = "openrouter"
            self._update_provider_ui()
            self.query_one("#connect-key-input").focus()
        elif event.button.id == "connect-do":
            self._do_connect()
        elif event.button.id == "connect-cancel":
            self.dismiss()

    def _do_connect(self):
        key = self.query_one("#connect-key-input").value.strip()
        if not key:
            # Try to use stored key
            stored = state.PROVIDER["gemini_api_key"] if self._selected_provider == "gemini" else state.PROVIDER["openrouter_api_key"]
            if not stored:
                self.query_one("#connect-status").update("  No key provided and no stored key found.")
                return
            provider.set_provider(self._selected_provider)
        else:
            base = "" if self._selected_provider == "gemini" else "https://openrouter.ai/api/v1"
            provider.set_key(self._selected_provider, key, base)

        if self._on_connect:
            self._on_connect(self._selected_provider)
        self.dismiss()

    def action_connect(self):
        self._do_connect()

    def action_cancel(self):
        self.dismiss()
