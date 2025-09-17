import asyncio
from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult

class InstallPage(Vertical):
    """Installation page that runs the real AntisOS shell installer."""

    def __init__(self, disk: str):
        super().__init__()
        # Sanitize disk input -> only keep the actual device path (/dev/xxx)
        self.disk = disk.split()[0].split("(")[0].strip()
        self.log_text = ""
        self.log_widget = Static("", id="install-log")

    def compose(self) -> ComposeResult:
        yield Static(f"Installing AntisOS to {self.disk}", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def log(self, message: str):
        """Append a message to the log widget."""
        self.log_text += f"\n{message}"
        self.log_widget.update(self.log_text)
        await asyncio.sleep(0.05)

    async def run_install_script(self):
        """Run the real shell installer at /usr/share/antisos-installer/install.sh."""
        script_path = "/usr/share/antisos-installer/install.sh"

        await self.log("Starting AntisOS installation...")
        await self.log(f"Target disk: {self.disk}")
        await self.log(f"Running {script_path} ...")

        try:
            process = await asyncio.create_subprocess_exec(
                script_path, self.disk,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            assert process.stdout is not None
            async for line in process.stdout:
                await self.log(line.decode().rstrip())

            await process.wait()
            if process.returncode == 0:
                await self.log("✅ Installation completed successfully!")
            else:
                await self.log(f"❌ Installer exited with code {process.returncode}")
        except FileNotFoundError:
            await self.log(f"[ERROR] Installer script not found at {script_path}")
        except PermissionError:
            await self.log(f"[ERROR] No permission to execute {script_path}. Try chmod +x.")

    async def on_mount(self) -> None:
        """Start installer automatically when the page is mounted."""
        asyncio.create_task(self.run_install_script())