from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button

class InstallPage(Vertical):
    """Simulated installation page without partitions."""

    def __init__(self, disk: str):
        super().__init__()
        self.disk = disk
        self.log_widget = Static("", id="install-log")
        self.log_text = ""

    def compose(self):
        yield Static(f"Installing AntisOS to {self.disk} (SIMULATION)", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")