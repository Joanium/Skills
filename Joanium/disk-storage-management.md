---
name: Disk & Storage Management — All Operating Systems
trigger: disk management, disk usage, df, du, disk full, partition, fdisk, lsblk, disk space, storage management, mount disk, format drive, check disk usage, SMART disk health, windows disk management, mac disk utility, disk partition linux, how much disk space
description: Manage disks and storage on Linux, macOS, and Windows — checking space usage, listing block devices, mounting and unmounting drives, partitioning, formatting, and checking disk health. Use when dealing with full disks, adding storage, diagnosing slow disks, or setting up new drives.
---

Disk management covers everything from checking what's using space, to adding and partitioning new drives, to diagnosing hardware failures. Knowing the right commands prevents accidental data loss.

## Linux Disk Management

### Checking Space Usage

```bash
# Disk usage by filesystem (human-readable)
df -h
# Output:
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1        50G   32G   16G  67% /
# /dev/sdb1       200G   80G  110G  40% /data
# tmpfs           7.8G     0  7.8G   0% /dev/shm

# Inodes (sometimes the problem — too many files, not file sizes)
df -i

# Show specific filesystem
df -h /home
df -h /var/log

# Disk Usage — what's taking space
du -sh /var/log/*          # size of each item in /var/log
du -sh /*                  # top-level directories (may take a moment)
du -sh ~/* 2>/dev/null | sort -rh | head -20   # largest items in home

# Interactive TUI disk usage browser (install ncdu first)
ncdu /               # browse entire filesystem interactively
ncdu /var/log        # browse a specific directory

# Find large files
find / -size +1G -type f 2>/dev/null | xargs ls -lh | sort -k5 -rh
find /var -size +100M -type f 2>/dev/null
```

### Listing Block Devices

```bash
# List all block devices (disks, partitions)
lsblk
# Output:
# NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
# sda      8:0    0   50G  0 disk
# ├─sda1   8:1    0   49G  0 part /
# └─sda2   8:2    0    1G  0 part [SWAP]
# sdb      8:16   0  200G  0 disk
# └─sdb1   8:17   0  200G  0 part /data

lsblk -f    # show filesystem types and UUIDs
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,UUID

# List with details
fdisk -l                   # detailed partition table info (requires root)
fdisk -l /dev/sda          # specific disk
parted -l                  # alternative to fdisk

# Disk identifiers
ls -la /dev/disk/by-id/    # persistent hardware-based IDs
ls -la /dev/disk/by-uuid/  # by filesystem UUID (recommended for fstab)
ls -la /dev/disk/by-path/  # by hardware path
```

### Mounting and Unmounting

```bash
# Mount a device
mount /dev/sdb1 /mnt/external
mount -t ext4 /dev/sdb1 /mnt/external     # specify filesystem type

# Mount a USB drive (find the device first with lsblk)
lsblk
mount /dev/sdc1 /mnt/usb

# Mount with options
mount -o ro /dev/sdb1 /mnt/backup          # read-only
mount -o uid=1000,gid=1000 /dev/sdc1 /mnt/usb  # for FAT/NTFS — set owner

# Mount an ISO file
mount -o loop image.iso /mnt/iso

# Unmount
umount /mnt/external
umount /dev/sdb1
# If "device is busy":
lsof /mnt/external         # find what's using it
fuser -m /mnt/external     # find processes
umount -l /mnt/external    # lazy unmount (detach when no longer busy)

# Show all mounts
mount                      # all current mounts
cat /proc/mounts           # same, from kernel
findmnt                    # tree view of mounts (modern)
findmnt /dev/sda1          # info about specific mount
```

### Partitioning

```bash
# INTERACTIVE — Choose one:
fdisk /dev/sdb             # MBR/GPT, classic, text menu
gdisk /dev/sdb             # GPT only, like fdisk but GPT-focused
parted /dev/sdb            # more features, scriptable
cfdisk /dev/sdb            # ncurses menu — easier for beginners

# SCRIPTED partitioning with parted
parted /dev/sdb --script mklabel gpt            # create GPT partition table
parted /dev/sdb --script mkpart primary ext4 1MiB 100%  # one big partition

# Check partition table
parted /dev/sdb print
```

### Formatting (Creating Filesystems)

```bash
# ⚠️ DESTRUCTIVE — all data on the partition is destroyed

# ext4 (standard Linux filesystem)
mkfs.ext4 /dev/sdb1
mkfs.ext4 -L "mydata" /dev/sdb1     # with volume label

# xfs (good for large files, used by RHEL by default)
mkfs.xfs /dev/sdb1
mkfs.xfs -L "mydata" /dev/sdb1

# btrfs (advanced — snapshots, compression, RAID)
mkfs.btrfs /dev/sdb1

# FAT32 (for USB drives compatible with all OSes)
mkfs.vfat -F32 /dev/sdc1
mkfs.fat -F32 -n "USBDRIVE" /dev/sdc1

# exFAT (modern cross-OS)
mkfs.exfat /dev/sdc1

# NTFS (for Windows compatibility)
mkfs.ntfs /dev/sdc1
```

### Disk Health (SMART)

```bash
# Install smartmontools
sudo apt install smartmontools

# Check SMART support and overall health
smartctl -i /dev/sda       # disk info
smartctl -H /dev/sda       # health status (PASSED or FAILED)
smartctl -a /dev/sda       # full SMART data

# Run a test
smartctl -t short /dev/sda    # quick test (1–2 minutes)
smartctl -t long /dev/sda     # full test (hours — worth doing on suspect drives)

# Check reallocated sectors (pre-failure indicator)
smartctl -A /dev/sda | grep -i "reallocated\|pending\|uncorrectable"

# For NVMe drives
smartctl -a /dev/nvme0n1
nvme smart-log /dev/nvme0n1   # requires nvme-cli package
```

### Swap Management

```bash
# View swap usage
swapon --show
free -h

# Create a swap file (when no swap partition)
fallocate -l 4G /swapfile          # create 4GB file
chmod 600 /swapfile                # must be 600
mkswap /swapfile                   # initialize
swapon /swapfile                   # enable

# Persist in /etc/fstab:
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Disable swap temporarily
swapoff -a

# Check what's using swap
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
    swap=$(cat /proc/$pid/status 2>/dev/null | awk '/VmSwap/{print $2}')
    [ -n "$swap" ] && [ "$swap" -gt 0 ] && echo "$pid $(cat /proc/$pid/comm) ${swap}kB"
done | sort -k3 -rn | head -10
```

---

## Windows Disk Management

### GUI Tools

```
Disk Management:     diskmgmt.msc
Storage Spaces:      System Settings → Storage
Disk Cleanup:        cleanmgr.exe
```

### Command Line

```batch
:: Show all disks and partitions
diskpart
  list disk
  select disk 1
  list partition
  list volume
  exit

:: Disk usage
dir C:\ /s /-c 2>nul | find "bytes"

:: Check filesystem for errors (requires restart for system drive)
chkdsk C: /f          :: fix errors
chkdsk C: /r          :: fix errors + scan for bad sectors (slow)
chkdsk D: /f /r       :: for non-system drives (can run immediately)

:: Format a drive (⚠️ DESTRUCTIVE)
format D: /fs:NTFS /q       :: quick format
format E: /fs:exFAT /q      :: exFAT

:: DISKPART for scripted operations
diskpart /s script.txt
```

```powershell
# PowerShell disk management
Get-Disk                           # list all disks
Get-Partition                      # list all partitions
Get-Volume                         # list all volumes with space info

# Disk usage per volume
Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free, Root

# Large files
Get-ChildItem C:\ -Recurse -ErrorAction SilentlyContinue |
    Sort-Object Length -Descending |
    Select-Object FullName, @{N='SizeMB';E={[math]::Round($_.Length/1MB,2)}} |
    Select-Object -First 20

# Initialize and format a new disk
Initialize-Disk -Number 1 -PartitionStyle GPT
New-Partition -DiskNumber 1 -UseMaximumSize -AssignDriveLetter |
    Format-Volume -FileSystem NTFS -NewFileSystemLabel "Data" -Confirm:$false

# Check disk health
Get-PhysicalDisk | Select-Object FriendlyName, HealthStatus, OperationalStatus, Size
Get-StorageReliabilityCounter -PhysicalDisk (Get-PhysicalDisk)[0]
```

---

## macOS Disk Management

### diskutil — The Main Tool

```bash
# List all disks and volumes
diskutil list
diskutil list /dev/disk0      # specific disk

# Info about a disk or partition
diskutil info /dev/disk0
diskutil info /dev/disk0s1

# Mount / Unmount
diskutil mount /dev/disk2s1
diskutil unmount /dev/disk2s1
diskutil eject /dev/disk2         # safe eject (unmount all + eject)

# Repair filesystem
diskutil repairVolume /dev/disk1s1
diskutil repairDisk /dev/disk1

# Format a disk (⚠️ DESTRUCTIVE)
diskutil eraseDisk APFS "MyDrive" /dev/disk2        # APFS (macOS modern)
diskutil eraseDisk HFS+ "MyDrive" /dev/disk2        # HFS+ (older macOS)
diskutil eraseDisk ExFAT "USB" /dev/disk2           # cross-platform
diskutil eraseDisk FAT32 "USB" MBRFormat /dev/disk2 # FAT32 with MBR

# Partition a disk
diskutil partitionDisk /dev/disk2 GPT \
    APFS "System" 100G \
    ExFAT "Data" R

# Check space
df -h
du -sh ~/Downloads/* | sort -rh | head -10
```

### Disk Utility (GUI)

```bash
open -a "Disk Utility"
# Handles: format, partition, RAID, repair, encryption (FileVault), disk images
```

---

## Cross-Platform Quick Reference

| Task | Linux | macOS | Windows |
|---|---|---|---|
| Show disk space | `df -h` | `df -h` | `Get-PSDrive` |
| Show what's using space | `du -sh /* \| sort -rh` | `du -sh ~/* \| sort -rh` | `Get-ChildItem C:\ -Recurse \| Sort Length` |
| List disks | `lsblk` | `diskutil list` | `Get-Disk` |
| Mount a drive | `mount /dev/sdb1 /mnt/d` | `diskutil mount /dev/disk2s1` | `diskpart` or auto |
| Format a partition | `mkfs.ext4 /dev/sdb1` | `diskutil eraseVolume APFS "name" /dev/disk2s1` | `Format-Volume` |
| Check disk health | `smartctl -H /dev/sda` | `diskutil repairVolume /dev/disk0s1` | `Get-StorageReliabilityCounter` |
| Check filesystem errors | `fsck /dev/sdb1` | `diskutil repairVolume` | `chkdsk D: /f` |
