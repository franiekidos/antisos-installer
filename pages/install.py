import asyncio
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static
from textual.app import ComposeResult

class InstallPage(Vertical):
    """Runs the standalone install.sh script and streams its logs."""

    def __init__(self, disk_label: str):
        """
        disk_label: The human-readable label from disk selection (e.g. "/dev/sda (67G SSD)")
        """
        super().__init__()
        self.disk_label = disk_label
        # Extract only the device path for the script
        self.disk_path = disk_label.split()[0]  # "/dev/sda"
        self.log_text = ""
        self.log_widget = Static("", id="install-log")

    def compose(self) -> ComposeResult:
        yield Static(f"Installing AntisOS to {self.disk_label}", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def log(self, message: str):
        """Append a message to the log and refresh the TUI."""
        self.log_text += f"\n{message}"
        self.log_widget.update(self.log_text)
        await asyncio.sleep(0.05)  # allow UI to refresh

    async def run_install_script(self, script_path="/usr/share/antisos-installer/install.sh"):
        """Execute the install.sh script and stream its output."""
        await self.log(f"Running {script_path} on {self.disk_path}...")
        process = await asyncio.create_subprocess_shell(
            f"bash '{script_path}' '{self.disk_path}'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert process.stdout is not None
        async for line in process.stdout:
            await self.log(line.decode().rstrip())
        await process.wait()
        if process.returncode != 0:
            await self.log(f"[ERROR] Script exited with code {process.returncode}")
        else:
            await self.log("Installation finished successfully!")

    async def on_mount(self):
        """Start installation automatically when the page mounts."""
        asyncio.create_task(self.run_install_script())
