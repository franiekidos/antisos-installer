import asyncio
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static
from textual.app import ComposeResult

class InstallPage(Vertical):
    """Installation page for AntisOS that runs the install.sh script."""

    def __init__(self, disk_label: str):
        super().__init__()
        self.disk_label = disk_label
        self.log_text = ""
        self.log_widget = Static("", id="install-log", expand=True)

    def compose(self) -> ComposeResult:
        yield Static(f"Installing AntisOS to {self.disk_label}", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def log(self, message: str):
        """Append a message to the log and refresh the TUI, auto-scrolling to bottom."""
        self.log_text += f"\n{message}"
        self.log_widget.update(self.log_text)
        # Scroll to the end so latest log is visible
        if hasattr(self.log_widget, "scroll_end"):
            self.log_widget.scroll_end(animate=False)
        await asyncio.sleep(0.01)  # small delay to allow TUI refresh

    async def run_install_script(self, script_path="/usr/share/antisos-installer/install.sh"):
        """Run the install.sh script and stream its stdout/stderr to the log."""
        await self.log(f"Running {script_path} on {self.disk_label}...")
        process = await asyncio.create_subprocess_shell(
            f"bash '{script_path}' '{self.disk_label}'",
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
        """Start the installation asynchronously when the page is mounted."""
        asyncio.create_task(self.run_install_script())

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle Quit button."""
        if event.button.id == "install-quit":
            from textual.app import App
            App.get_app().exit()
