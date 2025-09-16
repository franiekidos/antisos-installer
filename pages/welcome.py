from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button

class WelcomePage(Vertical):
    """Welcome screen."""

    def compose(self) -> ComposeResult:
        yield Static("Welcome to AntisOS Installer!", id="welcome-title")
        yield Static("This wizard will guide you through the installation.")

        with Horizontal():
            yield Button("Next", id="welcome-next")