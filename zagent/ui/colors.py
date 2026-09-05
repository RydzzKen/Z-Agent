"""ANSI color codes — OpenCode warm theme (truecolor + 256 fallback)."""

# ── helpers ──────────────────────────────────────────────────────────
def _fg(r, g, b): return f"\033[38;2;{r};{g};{b}m"
def _bg(r, g, b): return f"\033[48;2;{r};{g};{b}m"

# ── modifiers ────────────────────────────────────────────────────────
C_RESET   = "\033[0m"
C_BOLD    = "\033[1m"
C_DIM     = "\033[2m"
C_ITALIC  = "\033[3m"
C_UNDERL  = "\033[4m"

# ── warm theme palette (OpenCode-inspired) ───────────────────────────
# Background: near-black with reddish-brown undertone (#1e1a1a)
# Text: warm off-white (#fdfcfc)
C_BG        = _bg(30, 26, 26)
C_FG        = _fg(253, 252, 252)
C_FG_DIM    = _fg(154, 152, 152)   # muted gray
C_FG_MUTE   = _fg(100, 98, 98)     # more muted

# Semantic colors — warm Apple-HIG-inspired
C_PRIMARY   = _fg(0, 122, 255)     # blue
C_ACCENT    = _fg(255, 159, 10)    # orange
C_SUCCESS   = _fg(48, 209, 88)     # green
C_ERROR     = _fg(255, 59, 48)     # red
C_WARNING   = _fg(255, 159, 10)    # orange
C_INFO      = _fg(0, 122, 255)     # blue

# Aliases for backward compat with existing code
C_CYAN    = _fg(0, 198, 255)       # cyan accent
C_GREEN   = _fg(48, 209, 88)
C_YELLOW  = _fg(255, 214, 10)
C_BLUE    = _fg(0, 122, 255)
C_MAGENTA = _fg(191, 90, 242)
C_RED     = _fg(255, 59, 48)
C_WHITE   = _fg(253, 252, 252)
C_ORANGE  = _fg(255, 159, 10)

# ── border / UI element colors ───────────────────────────────────────
C_BORDER      = _fg(60, 56, 56)
C_BORDER_DIM  = _fg(44, 42, 42)
C_HIGHLIGHT   = _fg(255, 159, 10)  # orange highlight

# ── semantic aliases used by format helpers ───────────────────────────
C_USER_FG     = _fg(48, 209, 88)    # green for user label
C_AI_FG       = _fg(191, 90, 242)   # purple for AI label
C_TOOL_FG     = _fg(255, 159, 10)   # orange for tool names
C_THINK_FG    = _fg(255, 214, 10)   # yellow for thinking
C_READ_FG     = _fg(0, 198, 255)    # cyan for reads
C_WRITE_FG    = _fg(48, 209, 88)    # green for writes
C_COMPLETE_FG = _fg(253, 252, 252)  # white for completion
