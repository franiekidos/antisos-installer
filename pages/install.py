#!/usr/bin/env python3
import asyncio
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, scroll_view
from textual.widgets import Static, Button

class LogView(scroll_view):
    """Scrollable log widget using Static inside scroll_view."""
    def __init__(self):
        super().__init__()
        self.log_text = ""
        self.log_widget = Static("", id="log-text")
        self.mount(self.log_widget)

    async def write_line(self, line: str):
        self.log_text += line + "\n"
        self.log_widget.update(self.log_text)
        self.scroll_end(animate=False)
        await asyncio.sleep(0)  # Yield so UI refreshes

class InstallPage(Vertical):
    """Runs the installation script at /usr/share/antisos-installer/install.sh and displays logs."""

    def __init__(self):
        super().__init__()
        self.logview = LogView()

    def compose(self) -> ComposeResult:
        yield Static("Installing AntisOS...", id="install-title")
        yield self.logview
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def log(self, message: str):
        await self.logview.write_line(message)

    async def run_script(self):
        """Run the external shell script and stream output to the log."""
        script_path = "/usr/share/antisos-installer/install.sh"
        await self.log(f"Starting installation using {script_path}...")

        process = await asyncio.create_subprocess_shell(
            script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        assert process.stdout is not None
        async for line in process.stdout:
            await self.log(line.decode().rstrip())

        await process.wait()
        if process.returncode == 0:
            await self.log("Installation finished successfully!")
        else:
            await self.log(f"[ERROR] Installation failed with code {process.returncode}")

    async def on_mount(self) -> None:
        """Automatically start the script when the page is mounted."""
        await self.run_script()