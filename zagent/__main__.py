"""Allow running Z-Agent as `python -m zagent`."""
import sys

def main():
    # Check for --tui flag or ZAGENT_TUI env var
    if "--tui" in sys.argv or __import__("os").environ.get("ZAGENT_TUI"):
        from .ui.tui import run_tui
        run_tui()
    else:
        from .main import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
