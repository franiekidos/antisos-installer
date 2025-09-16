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

        # 🔑 Extract the real device path (strip anything in parentheses)
        device_path = self.disk.split()[0]
        await self.log(f"Using device: {device_path}")

        # 1. Create a single root partition on the disk
        await self.log(f"Creating a single ext4 partition on {device_path}...")
        await self.run_command(f"parted -s {device_path} mklabel gpt")
        await self.run_command(f"parted -s -a optimal {device_path} mkpart primary ext4 1MiB 100%")
        root_partition = f"{device_path}1"

        # 2. Format the partition
        await self.log(f"Formatting partition {root_partition} as ext4...")
        await self.run_command(f"mkfs.ext4 -F {root_partition}")

        # 3. Mount the partition
        mount_point = "/mnt"
        await self.log(f"Mounting {root_partition} to {mount_point}...")
        await self.run_command(f"mount {root_partition} {mount_point}")

        # 4. Install base Arch Linux system
        await self.log("Installing base system packages...")
        await self.run_command(f"pacstrap {mount_point} base linux linux-firmware vim")

        # 5. Generate fstab
        await self.log("Generating fstab...")
        await self.run_command(f"genfstab -U {mount_point} >> {mount_point}/etc/fstab")

        # 6. Configure system in chroot
        await self.log("Configuring system inside chroot...")
        chroot_cmds = [
            f"arch-chroot {mount_point} ln -sf /usr/share/zoneinfo/US/Pacific /etc/localtime",
            f"arch-chroot {mount_point} hwclock --systohc",
            f"arch-chroot {mount_point} sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen",
            f"arch-chroot {mount_point} locale-gen",
            f"arch-chroot {mount_point} bash -c \"echo 'LANG=en_US.UTF-8' > /etc/locale.conf\"",
            f"arch-chroot {mount_point} bash -c \"echo 'antisos' > /etc/hostname\"",
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
                await self.log("Legacy BIOS detected. Installing GRUB...")
                await self.run_command(f"arch-chroot {mount_point} grub-install --target=i386-pc {device_path}")
                await self.run_command(f"arch-chroot {mount_point} grub-mkconfig -o /boot/grub/grub.cfg")

            # 8. Setup root autologin on tty1
            await self.log("Configuring root autologin on tty1...")
            service_override = f"{mount_point}/etc/systemd/system/getty@tty1.service.d"
            await self.run_command(f"mkdir -p {service_override}")
            override_conf = f"{service_override}/override.conf"
            await self.run_command(
                f"bash -c \"echo -e '[Service]\\nExecStart=\\nExecStart=-/sbin/agetty --autologin root --noclear %I $TERM' > {override_conf}\""
            )

            # 9. Done
            await self.log("✅ Installation complete! System is set to autologin as root on tty1.")
        except Exception as e:
            await self.log(f"❌ Installation failed: {e}")
