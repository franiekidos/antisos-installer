import asyncio
from textual.widgets import Static
from textual.containers import Vertical, Horizontal
from textual.widgets import Button
from textual.app import ComposeResult

class InstallPage(Vertical):
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

    async def log(self, message: str):
        self.log_text += f"\n{message}"
        self.log_widget.update(self.log_text)
        await asyncio.sleep(0.05)

    async def run_command_stream(self, cmd: str):
        """Run a command and stream stdout/stderr line by line."""
        await self.log(f"$ {cmd}")
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
            raise RuntimeError(f"Command failed: {cmd}")

    async def run_install(self):
        await self.log("Starting AntisOS installation...")

        # Example: creating root partition (replace with actual device handling)
        root_partition = f"{self.disk}1"
        await self.run_command_stream(f"parted -s {self.disk} mklabel gpt")
        await self.run_command_stream(f"parted -s -a optimal {self.disk} mkpart primary ext4 1MiB 100%")
        await self.run_command_stream(f"mkfs.ext4 {root_partition}")
        await self.run_command_stream(f"mount {root_partition} /mnt")

        # Install base system with --noconfirm to avoid blocking
        await self.log("Installing base packages...")
        await self.run_command_stream("pacstrap /mnt base linux linux-firmware vim --noconfirm")

        # Generate fstab
        await self.run_command_stream("genfstab -U /mnt >> /mnt/etc/fstab")

        await self.log("Chrooting to configure system...")
        chroot_cmds = [
            "ln -sf /usr/share/zoneinfo/US/Pacific /etc/localtime",
            "hwclock --systohc",
            "sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen",
            "locale-gen",
            "echo 'LANG=en_US.UTF-8' > /etc/locale.conf",
            "echo 'antisos' > /etc/hostname",
        ]
        for cmd in chroot_cmds:
            await self.run_command_stream(f"arch-chroot /mnt {cmd}")

        # Detect UEFI/BIOS and install bootloader
        is_uefi = False
        try:
            with open("/sys/firmware/efi/efivars"):
                is_uefi = True
        except FileNotFoundError:
            is_uefi = False

        if is_uefi:
            await self.log("UEFI detected, installing systemd-boot...")
            await self.run_command_stream("arch-chroot /mnt bootctl install")
        else:
            await self.log("Legacy BIOS detected, installing GRUB...")
            await self.run_command_stream(f"arch-chroot /mnt grub-install --target=i386-pc {self.disk}")
            await self.run_command_stream("arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg")

        await self.log("Installation complete! You can reboot now.")
