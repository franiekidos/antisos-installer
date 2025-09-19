import asyncio
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button

class InstallPage(Vertical):
    def __init__(self, script_path: str = "/usr/share/antisos-installer/install.sh", display_lines: int = 20):
        super().__init__()
        self.script_path = script_path
        self.display_lines = display_lines
        self.log_lines = []
        self.log_widget = Static("", id="install-log")

    def compose(self) -> ComposeResult:
        yield Static(f"Running installer: {self.script_path}", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def log(self, message: str):
        """Append a line to the log and auto-scroll to show latest lines."""
        self.log_lines.append(message)
        # Only display the last `display_lines` lines to simulate scrolling
        visible_lines = self.log_lines[-self.display_lines:]
        self.log_widget.update("\n".join(visible_lines))
        await asyncio.sleep(0.01)

    async def run_script(self):
        """Run the shell script and stream stdout/stderr line by line."""
        try:
            process = await asyncio.create_subprocess_shell(
                f"bash {self.script_path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            assert process.stdout is not None
            async for line in process.stdout:
                await self.log(line.decode().rstrip())
            await process.wait()
            await self.log(f"\nInstaller finished with exit code {process.returncode}")
        except Exception as e:
            await self.log(f"[ERROR]: {e}")

    async def on_mount(self):
        """Start the installer script automatically when the page is mounted."""
        asyncio.create_task(self.run_script())