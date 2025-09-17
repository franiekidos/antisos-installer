import asyncio
from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult

class InstallPage(Vertical):
    """Installation page that executes the real AntisOS shell installer with live feedback."""

    def __init__(self, disk: str):
        super().__init__()
        self.disk = disk
        self.log_text = ""  # Stores all log messages for display
        self.log_widget = Static("", id="install-log")

    def compose(self) -> ComposeResult:
        """Compose the TUI elements for this page."""
        yield Static(f"Installing AntisOS to {self.disk}", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def log(self, message: str):
        """
        Append a message to the log widget.
        This ensures that every step is visible to the user.
        """
        self.log_text += f"\n{message}"
        self.log_widget.update(self.log_text)
        await asyncio.sleep(0.05)  # Small delay to allow TUI to refresh

    async def run_install_script(self):
        """
        Run the real shell installer asynchronously.
        Streams stdout and stderr line by line to the TUI log widget.
        """
        await self.log("Starting installation process...")
        await self.log(f"Target disk: {self.disk}")
        await self.log("Launching installer script...")

        # Ensure the script is executable
        script_path = "/usr/share/antisos-installer/install.sh"
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
                await self.log("Please check the logs and try again.")
        except FileNotFoundError:
            await self.log(f"[ERROR] Installer script not found at {script_path}.")
        except PermissionError:
            await self.log(f"[ERROR] No permission to execute {script_path}. Make it executable.")

    async def on_mount(self) -> None:
        """Automatically start installation when the page is mounted."""
        # Run the shell installer asynchronously so the TUI stays responsive
        asyncio.create_task(self.run_install_script())