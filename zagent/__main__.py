"""Allow running Z-Agent as `python -m zagent`."""
import sys

def main():
    # Default: TUI. Gunakan --cli / ZAGENT_CLI=1 untuk mode terminal biasa.
    if "--cli" in sys.argv or __import__("os").environ.get("ZAGENT_CLI"):
        from .main import main as cli_main
        cli_main()
    else:
        from .ui.tui import run_tui
        run_tui()


if __name__ == "__main__":
    main()