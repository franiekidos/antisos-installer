#!/usr/bin/env python3
import subprocess
import os
import shutil

def detect_boot_mode() -> str:
    """Detect if system booted in UEFI or Legacy."""
    return "uefi" if os.path.isdir("/sys/firmware/efi") else "legacy"

def detect_other_os() -> bool:
    """Detect if another OS is installed by checking EFI partitions or Linux/Windows partitions."""
    try:
        result = subprocess.run(
            ["lsblk", "-no", "FSTYPE,MOUNTPOINT"],
            capture_output=True, text=True
        ).stdout.splitlines()
        for line in result:
            fstype, *mount = line.split()
            if fstype in ["vfat", "ntfs"] or (mount and mount[0] not in ["", "/"]):
                return True
        return False
    except Exception:
        return False

def install_antisos(disk: str):
    print(f"[+] Installing AntisOS to {disk}...")

    # 1. Format disk
    subprocess.run(["mkfs.ext4", disk], check=True)

    # 2. Mount root
    os.makedirs("/mnt/antisos", exist_ok=True)
    subprocess.run(["mount", disk, "/mnt/antisos"], check=True)

    # 3. Install base Arch system
    subprocess.run(["pacstrap", "/mnt/antisos", "base", "linux", "linux-firmware"], check=True)

    # 4. Generate fstab
    with open("/mnt/antisos/etc/fstab", "w") as fstab:
        subprocess.run(["genfstab", "-U", "/mnt/antisos"], stdout=fstab, check=True)

    # 5. Chroot: locales, timezone, hostname
    chroot_cmds = [
        "ln -sf /usr/share/zoneinfo/US/Pacific /etc/localtime",
        "hwclock --systohc",
        "echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen",
        "locale-gen",
        "echo 'LANG=en_US.UTF-8' > /etc/locale.conf",
        "echo 'antis' > /etc/hostname",
    ]
    for cmd in chroot_cmds:
        subprocess.run(["arch-chroot", "/mnt/antisos", "bash", "-c", cmd], check=True)

    # 6. Bootloader setup
    mode = detect_boot_mode()
    other_os = detect_other_os()
    print(f"[+] Boot mode: {mode}, Other OS detected: {other_os}")

    if mode == "uefi":
        if other_os:
            # Dual-boot: use rEFInd
            print("[+] Installing rEFInd for dual-boot...")
            subprocess.run(["arch-chroot", "/mnt/antisos", "pacman", "-S", "--noconfirm", "refind-efi"], check=True)
            subprocess.run(["arch-chroot", "/mnt/antisos", "refind-install"], check=True)
        else:
            # Only AntisOS: systemd-boot
            print("[+] Installing systemd-boot...")
            subprocess.run(["arch-chroot", "/mnt/antisos", "bootctl", "install"], check=True)
            # Create loader.conf
            loader_conf = "/mnt/antisos/boot/loader/loader.conf"
            os.makedirs(os.path.dirname(loader_conf), exist_ok=True)
            with open(loader_conf, "w") as f:
                f.write("default antisos\n")
            with open("/mnt/antisos/boot/loader/entries/antisos.conf", "w") as f:
                f.write(
                    "title   AntisOS\n"
                    "linux   /vmlinuz-linux\n"
                    "initrd  /initramfs-linux.img\n"
                    "options root=/dev/sda rw\n"
                )
    else:
        # Legacy BIOS: GRUB
        subprocess.run(["arch-chroot", "/mnt/antisos", "grub-install", "--target=i386-pc", disk], check=True)
        subprocess.run(["arch-chroot", "/mnt/antisos", "grub-mkconfig", "-o", "/boot/grub/grub.cfg"], check=True)

    print("[+] Installation complete! Reboot to your new system.")