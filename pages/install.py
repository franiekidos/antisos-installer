import asyncio
import subprocess
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

class InstallPage(Vertical):
    """Installation page that runs the real install.sh script."""

    def __init__(self, disk: str):
        super().__init__()
        self.disk = disk
        self.log_text = ""
        self.log_widget = Static("", id="install-log")

    def compose(self) -> ComposeResult:
        yield Static(f"Installing AntisOS to {self.disk}", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def log(self, message: str):
        """Append message to the log widget and refresh."""
        self.log_text += f"\n{message}"
        self.log_widget.update(self.log_text)
        await asyncio.sleep(0.05)

    async def run_shell_script(self, script_path: str):
        """Run the shell script and stream its output to the log."""
        await self.log(f"Starting installer: {script_path}")
        process = await asyncio.create_subprocess_exec(
            script_path,
            self.disk,
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
            await self.log(f"[ERROR] Installer exited with code {process.returncode}")

    async def on_mount(self):
        # Start the shell-based installation in the background
        asyncio.create_task(self.run_shell_script("/usr/share/antisos-installer/install.sh"))
