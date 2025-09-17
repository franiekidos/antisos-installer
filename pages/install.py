#!/usr/bin/env python3
import asyncio
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button

class InstallPage(Vertical):
    """Runs /usr/share/antisos-installer/install.sh with auto-scrolling log."""

    def __init__(self, disk: str):
        super().__init__()
        self.disk = disk  # store the target disk
        self.log_text = ""
        self.log_widget = Static("", id="install-log", expand=True)

    def compose(self) -> ComposeResult:
        yield Static(f"Installing AntisOS to {self.disk}", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def log(self, message: str):
        self.log_text += message + "\n"
        self.log_widget.update(self.log_text)
        self.log_widget.scroll_end(animate=False)
        await asyncio.sleep(0)

    async def run_script(self):
        script_path = "/usr/share/antisos-installer/install.sh"
        await self.log(f"Running {script_path} on {self.disk}...\n")

        process = await asyncio.create_subprocess_shell(
            f"{script_path} {self.disk}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        assert process.stdout is not None
        async for line in process.stdout:
            await self.log(line.decode().rstrip())

        await process.wait()
        if process.returncode == 0:
            await self.log("\nInstallation finished successfully!")
        else:
            await self.log(f"\n[ERROR] Installation failed with code {process.returncode}")

    async def on_mount(self) -> None:
        await self.run_script()