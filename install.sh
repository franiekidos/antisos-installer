#!/usr/bin/env bash
set -euo pipefail

# =============================
# Variables
# =============================
DISK="$1"
MOUNTPOINT="/mnt"
UEFI_PARTITION=""
ROOT_PARTITION=""

# Function to log messages
log() {
    echo "[INSTALLER] $*"
}

# =============================
# 1️⃣ Detect firmware
# =============================
if [ -d /sys/firmware/efi/efivars ]; then
    FIRMWARE="UEFI"
    log "Firmware detected: UEFI"
else
    FIRMWARE="BIOS"
    log "Firmware detected: Legacy BIOS"
fi

# =============================
# 2️⃣ Partition the disk
# =============================
log "Creating partitions on $DISK..."
if [ "$FIRMWARE" = "UEFI" ]; then
    # Create GPT and EFI partition
    parted -s "$DISK" mklabel gpt
    parted -s -a optimal "$DISK" mkpart ESP fat32 1MiB 551MiB
    parted -s "$DISK" set 1 boot on
    EFI_PARTITION="${DISK}1"
    parted -s -a optimal "$DISK" mkpart primary ext4 551MiB 100%
    ROOT_PARTITION="${DISK}2"
else
    # Legacy BIOS: single root partition
    parted -s "$DISK" mklabel msdos
    parted -s -a optimal "$DISK" mkpart primary ext4 1MiB 100%
    ROOT_PARTITION="${DISK}1"
fi

# =============================
# 3️⃣ Format partitions
# =============================
if [ "$FIRMWARE" = "UEFI" ]; then
    log "Formatting EFI partition as FAT32..."
    mkfs.fat -F32 "$EFI_PARTITION"
fi
log "Formatting root partition as ext4..."
mkfs.ext4 "$ROOT_PARTITION"

# =============================
# 4️⃣ Mount partitions
# =============================
log "Mounting root partition to $MOUNTPOINT..."
mount "$ROOT_PARTITION" "$MOUNTPOINT"
if [ "$FIRMWARE" = "UEFI" ]; then
    log "Mounting EFI partition..."
    mkdir -p "$MOUNTPOINT/boot"
    mount "$EFI_PARTITION" "$MOUNTPOINT/boot"
fi

# =============================
# 5️⃣ Install base system
# =============================
log "Installing base system..."
pacstrap "$MOUNTPOINT" base linux linux-firmware vim --noconfirm

# =============================
# 6️⃣ Generate fstab
# =============================
log "Generating fstab..."
genfstab -U "$MOUNTPOINT" >> "$MOUNTPOINT/etc/fstab"

# =============================
# 7️⃣ Chroot configuration
# =============================
log "Configuring system in chroot..."
arch-chroot "$MOUNTPOINT" ln -sf /usr/share/zoneinfo/US/Pacific /etc/localtime
arch-chroot "$MOUNTPOINT" hwclock --systohc
arch-chroot "$MOUNTPOINT" sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
arch-chroot "$MOUNTPOINT" locale-gen
echo "LANG=en_US.UTF-8" > "$MOUNTPOINT/etc/locale.conf"
echo "antisos" > "$MOUNTPOINT/etc/hostname"

# =============================
# 8️⃣ Bootloader installation
# =============================
if [ "$FIRMWARE" = "UEFI" ]; then
    log "Installing systemd-boot..."
    arch-chroot "$MOUNTPOINT" bootctl install
else
    log "Installing GRUB for legacy BIOS..."
    arch-chroot "$MOUNTPOINT" pacman -Sy grub --noconfirm
    arch-chroot "$MOUNTPOINT" grub-install --target=i386-pc "$DISK"
    arch-chroot "$MOUNTPOINT" grub-mkconfig -o /boot/grub/grub.cfg
fi

# =============================
# 9️⃣ Finish installation
# =============================
log "Installation complete! You can reboot now."

# =============================
# Notes:
# - The script expects to run as root.
# - DISK should be unmounted and safe to write.
# - All output is prefixed with [INSTALLER] for TUI logging.
# - Additional features like optional packages or advanced partitioning
#   can be added modularly.