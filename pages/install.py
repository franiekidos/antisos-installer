import asyncio
from textual.widgets import Static
from textual.containers import Vertical, Horizontal
from textual.widgets import Button
from textual.app import ComposeResult

class InstallPage(Vertical):
    """Installation page that runs the external AntisOS install script."""

    def __init__(self, disk_label: str):
        super().__init__()
        self.disk = disk_label.split()[0]  # Only use the raw device path
        self.log_text = ""
        self.log_widget = Static("", id="install-log")

    def compose(self) -> ComposeResult:
        yield Static(f"Installing AntisOS to {self.disk}", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def log(self, message: str):
        self.log_text += f"\n{message}"
        self.log_widget.update(self.log_text)
        await asyncio.sleep(0.05)

    async def run_install_script(self):
        """Run the external shell installer script and stream its output."""
        script_path = "/usr/share/antisos-installer/install.sh"
        cmd = f"bash {script_path} {self.disk}"
        await self.log(f"Currently Running: {cmd}")

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert process.stdout is not None
        async for line in process.stdout:
            await self.log(line.decode().rstrip())

        await process.wait()
        if process.returncode != 0:
            await self.log(f"[ERROR] Installer exited with code {process.returncode}")
        else:
            await self.log("Installation complete! You can reboot now.")

    async def on_mount(self) -> None:
        await self.run_install_script()