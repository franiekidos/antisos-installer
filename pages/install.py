#!/usr/bin/env python3
import asyncio
import subprocess
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static
from textual.app import ComposeResult
from textual.widget import Widget


class InstallPage(Vertical):
    """Installation page that runs actual system install steps."""

    def __init__(self, disk: str, partition: str):
        super().__init__()
        self.disk = disk
        self.partition = partition
        self.log_text = ""
        self.log_widget = Static("", id="install-log")

    def compose(self) -> ComposeResult:
        yield Static(f"Installing AntisOS to {self.partition or self.disk}", id="install-title")
        yield self.log_widget
        with Horizontal():
            yield Button("Quit", id="install-quit")

    async def on_mount(self) -> None:
        await self.run_install()

    async def log(self, message: str):
        """Append a message to the log widget."""
        self.log_text += f"\n{message}"
        self.log_widget.update(self.log_text)
        await asyncio.sleep(0.5)  # allow UI to refresh

    async def run_command(self, cmd: str, check=True):
        """Run a shell command asynchronously and log output."""
        await self.log(f"$ {cmd}")
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
            if stdout:
                await self.log(stdout.decode())
            if check and proc.returncode != 0:
                raise RuntimeError(f"Command failed: {cmd}")
        except Exception as e:
            await self.log(f"[ERROR] {e}")
            raise

    async def run_install(self):
        """Run the full installation process."""
        try:
            await self.log("Starting installation...")

            # 1. Format the partition
            await self.log("Formatting partition...")
            fs_cmd = f"mkfs.ext4 {self.partition}"  # simple placeholder
            await self.run_command(fs_cmd)

            # 2. Mount partition
            await self.log("Mounting partition...")
            mount_point = "/mnt"
            await self.run_command(f"mount {self.partition} {mount_point}")

            # 3. Install base system
            await self.log("Installing base Arch system...")
            await self.run_command(f"pacstrap {mount_point} base linux linux-firmware")

            # 4. Generate fstab
            await self.log("Generating fstab...")
            await self.run_command(f"genfstab -U {mount_point} >> {mount_point}/etc/fstab")

            # 5. Chroot for system configuration
            await self.log("Entering chroot for configuration...")
            # Example: setup locale, timezone, hostname
            chroot_cmds = [
                f"arch-chroot {mount_point} ln -sf /usr/share/zoneinfo/US/Pacific /etc/localtime",
                f"arch-chroot {mount_point} hwclock --systohc",
                f"arch-chroot {mount_point} sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen",
                f"arch-chroot {mount_point} locale-gen",
                f"arch-chroot {mount_point} echo 'antisos' > {mount_point}/etc/hostname",
            ]
            for cmd in chroot_cmds:
                await self.run_command(cmd)

            # 6. Bootloader installation
            await self.log("Detecting firmware and installing bootloader...")
            # Detect UEFI
            try:
                with open("/sys/firmware/efi/efivars") as f:
                    is_uefi = True
            except FileNotFoundError:
                is_uefi = False

            if is_uefi:
                await self.log("UEFI detected: installing systemd-boot")
                await self.run_command(f"arch-chroot {mount_point} bootctl install")
            else:
                await self.log("Legacy BIOS detected: installing GRUB")
                await self.run_command(f"arch-chroot {mount_point} grub-install --target=i386-pc {self.disk}")
                await self.run_command(f"arch-chroot {mount_point} grub-mkconfig -o /boot/grub/grub.cfg")

            await self.log("Installation complete! You can reboot now.")
        except Exception as e:
            await self.log(f"Installation failed: {e}")
