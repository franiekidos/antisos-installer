#!/usr/bin/env python3
import asyncio
import subprocess
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static
from textual.app import ComposeResult


class InstallPage(Vertical):
    """Installation page for AntisOS that runs a full Arch Linux installation."""

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

    async def on_mount(self) -> None:
        await self.run_install()

    async def log(self, message: str):
        """Append a message to the log widget and update TUI."""
        self.log_text += f"\n{message}"
        self.log_widget.update(self.log_text)
        await asyncio.sleep(0.5)  # Small delay to allow UI to refresh

    async def run_command(self, cmd: str, check=True):
        """Execute a shell command asynchronously and log output."""
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
        """Run the full installation process for AntisOS."""
        try:
            await self.log("Starting AntisOS installation...")

            # 1. Create a single root partition on the disk
            await self.log(f"Creating a single ext4 partition on {self.disk}...")
            # Use parted to create GPT and a root partition
            await self.run_command(f"parted {self.disk} mklabel gpt")
            await self.run_command(f"parted -a optimal {self.disk} mkpart primary ext4 1MiB 100%")
            root_partition = f"{self.disk}1"

            # 2. Format the partition
            await self.log(f"Formatting partition {root_partition} as ext4...")
            await self.run_command(f"mkfs.ext4 {root_partition}")

            # 3. Mount the partition
            await self.log(f"Mounting {root_partition} to /mnt...")
            mount_point = "/mnt"
            await self.run_command(f"mount {root_partition} {mount_point}")

            # 4. Install base Arch Linux system
            await self.log("Installing base system packages...")
            await self.run_command(f"pacstrap {mount_point} base linux linux-firmware vim")

            # 5. Generate fstab
            await self.log("Generating fstab...")
            await self.run_command(f"genfstab -U {mount_point} >> {mount_point}/etc/fstab")

            # 6. Configure system in chroot
            await self.log("Entering chroot for system configuration...")
            chroot_cmds = [
                # Timezone
                f"arch-chroot {mount_point} ln -sf /usr/share/zoneinfo/US/Pacific /etc/localtime",
                f"arch-chroot {mount_point} hwclock --systohc",
                # Locale
                f"arch-chroot {mount_point} sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen",
                f"arch-chroot {mount_point} locale-gen",
                f"arch-chroot {mount_point} echo 'LANG=en_US.UTF-8' > {mount_point}/etc/locale.conf",
                # Hostname
                f"arch-chroot {mount_point} echo 'antisos' > {mount_point}/etc/hostname",
            ]
            for cmd in chroot_cmds:
                await self.run_command(cmd)

            # 7. Bootloader detection and installation
            await self.log("Detecting firmware and installing bootloader...")
            is_uefi = False
            try:
                with open("/sys/firmware/efi/efivars"):
                    is_uefi = True
            except FileNotFoundError:
                is_uefi = False

            if is_uefi:
                await self.log("UEFI detected. Installing systemd-boot...")
                await self.run_command(f"arch-chroot {mount_point} bootctl install")
            else:
                await self.log("Legacy BIOS detected. Installing GRUB Legacy...")
                await self.run_command(f"arch-chroot {mount_point} grub-install --target=i386-pc {self.disk}")
                await self.run_command(f"arch-chroot {mount_point} grub-mkconfig -o /boot/grub/grub.cfg")

            # 8. Final messages
            await self.log("Setting up initial user and finishing configuration...")
            await self.run_command(f"arch-chroot {mount_point} useradd -m -G wheel liveuser")
            await self.run_command(f"arch-chroot {mount_point} passwd liveuser")

            await self.log("Installation complete! You can reboot into your new AntisOS system.")
        except Exception as e:
            await self.log(f"Installation failed: {e}")
