import asyncio
from textual.widgets import TextLog, Button, Static
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult

class InstallPage(Vertical):
    def __init__(self, disk: str):
        super().__init__()
        self.disk = disk.split()[0].split("(")[0].strip()
        self.log_widget = TextLog(id="install-log", highlight=True, wrap=True)

    def compose(self) -> ComposeResult:
        yield Static(f"Installing AntisOS to {self.disk}", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def log(self, message: str):
        self.log_widget.write(message)
        await asyncio.sleep(0.02)

    async def run_install_script(self):
        script_path = "/usr/share/antisos-installer/install.sh"

        await self.log("Starting AntisOS installation...")
        await self.log(f"Target disk: {self.disk}")

        try:
            process = await asyncio.create_subprocess_exec(
                script_path, self.disk,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
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
            await self.log(f"[ERROR] {script_path} not found")
        except PermissionError:
            await self.log(f"[ERROR] Permission denied for {script_path}")

    async def on_mount(self) -> None:
        asyncio.create_task(self.run_install_script())