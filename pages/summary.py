from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult

class SummaryPage(Vertical):
    """Summary page."""

    def __init__(self, disk: str):
        super().__init__()
        self.disk = disk

    def compose(self) -> ComposeResult:
        yield Static("Summary", id="summary-title")
        yield Static(f"Disk: {self.disk}")
        with Horizontal():
            yield Button("Back", id="summary-back")
            yield Button("Install", id="summary-install")