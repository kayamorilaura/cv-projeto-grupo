"""Console output with an optional Rich formatter."""

from datetime import datetime

try:
    from rich.console import Console
except ImportError:
    Console = None


console = Console() if Console is not None else None


def log(message: str, style: str = "cyan") -> None:
    """Print a timestamped message, using Rich styling when available."""
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
    if console is not None:
        console.print(line, style=style)
    else:
        print(line)
