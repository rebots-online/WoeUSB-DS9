<div align="center">
<h1>WoeUSB-ng</h1>
<img src=".github/woeusb-logo.png" alt="brand" width="28%" />
</div>

_A Linux program to create a Windows USB stick installer from a real Windows DVD or image._

**NEW: WoeUSB-DS9 now supports large ISO files (>4GB) through NTFS, exFAT, F2FS and BTRFS filesystem support!**

This package contains two programs:

* **woeusb**: A command-line utility that enables you to create your own bootable Windows installation USB storage device from an existing Windows Installation disc or disk image
* **woeusbgui**: Graphic version of woeusb

Supported images:

Windows Vista, Windows 7, Window 8.x, Windows 10. All languages and any version (home, pro...) and Windows PE are supported.

Supported bootmodes:

* Legacy/MBR-style/IBM PC compatible bootmode
* Native UEFI booting is supported for Windows 7 and later images 
* Support for multiple filesystems (FAT32, NTFS, exFAT, F2FS, BTRFS) with automatic selection based on ISO content

This project rewrite of original [WoeUSB](https://github.com/slacka/WoeUSB) 

## Installation

### Arch
```shell
yay -S woeusb-ng
```

### For other distributions

### 1. Install WoeUSB-ng's Dependencies
#### Ubuntu

```shell
sudo apt install git p7zip-full python3-pip python3-wxgtk4.0 grub2-common grub-pc-bin parted dosfstools ntfs-3g exfat-utils f2fs-tools btrfs-progs
```

#### Fedora (tested on: Fedora Workstation 33)
```shell
sudo dnf install git p7zip p7zip-plugins python3-pip python3-wxpython4
```

### 2. Install WoeUSB-ng
```shell
sudo pip3 install WoeUSB-ng
```

## Installation from source code

### 1. Install WoeUSB-ng's Build Dependencies
#### Ubuntu
```shell
sudo apt install git p7zip-full python3-pip python3-wxgtk4.0 grub2-common grub-pc-bin parted dosfstools ntfs-3g exfat-utils f2fs-tools btrfs-progs
```
#### Arch
```shell
sudo pacman -Suy p7zip python-pip python-wxpython ntfs-3g exfatprogs f2fs-tools btrfs-progs
```
#### Fedora (tested on: Fedora Workstation 33) 
```shell
sudo dnf install git p7zip p7zip-plugins python3-pip python3-wxpython4
```
### 2. Install WoeUSB-ng
```shell
git clone https://github.com/WoeUSB/WoeUSB-ng.git
cd WoeUSB-ng
sudo pip3 install .
```

## Installation from source code locally or in virtual environment 
```shell
git clone https://github.com/WoeUSB/WoeUSB-ng.git
cd WoeUSB-ng
git apply development.patch
sudo pip3 install -e .
```
Please note that this will not create menu shortcut and you may need to run gui twice as it may want to adjust policy. 

## Uninstalling

To remove WoeUSB-ng completely run (needed only when using installation from source code):
```shell
sudo pip3 uninstall WoeUSB-ng
sudo rm /usr/share/icons/WoeUSB-ng/icon.ico \
    /usr/share/applications/WoeUSB-ng.desktop \
    /usr/local/bin/woeusbgui
sudo rmdir /usr/share/icons/WoeUSB-ng/
```

## Advanced Filesystem Features

WoeUSB-DS9 automatically detects if your Windows ISO contains files larger than 4GB and selects the appropriate filesystem:

| Filesystem | Used When | Requirements |
|------------|-----------|--------------|
| FAT32      | Default for maximum compatibility | dosfstools package |
| NTFS       | ISO contains files >4GB | ntfs-3g package |
| exFAT      | ISO contains files >4GB | exfat-utils/exfatprogs package |
| F2FS       | ISO contains files >4GB | f2fs-tools package |
| BTRFS      | ISO contains files >4GB | btrfs-progs package |

The filesystem is automatically selected based on the detected content and available tools, with a preference order of exFAT > NTFS > F2FS > BTRFS > FAT32.

For detailed information on implementation, see the IMPLEMENTATION_SUMMARY.md file.
## License
WoeUSB-ng is distributed under the [GPL license](https://github.com/WoeUSB/WoeUSB-ng/blob/master/COPYING).
