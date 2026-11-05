"""Console output with an optional Rich formatter."""

from datetime import datetime

try:
    from rich.console import Console
except ImportError:
    Console = None


class AppLogger:
    """Print timestamped messages with optional Rich styling."""

    def __init__(self) -> None:
        if Console is not None:
            self.console = Console()
        else:
            self.console = None

    def info(self, message: str, style: str = "cyan") -> None:
        """Print a message, using the requested style when Rich is available."""
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        if self.console is not None:
            self.console.print(line, style=style)
        else:
            print(line)
