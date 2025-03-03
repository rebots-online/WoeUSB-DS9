# WoeUSB-DS9

<div align="center">
<img src=".github/woeusb-logo.png" alt="brand" width="28%" />
</div>

_A Linux program to create advanced Windows USB installation media with extended filesystem support, multi-boot capabilities, and Windows-To-Go functionality._

## Features

WoeUSB-DS9 enables you to create bootable Windows USB drives with advanced capabilities:

### Core Functionality
* Create bootable Windows installation USB from ISO images or DVDs
* Support for Windows Vista through Windows 11
* Compatible with both Legacy BIOS and UEFI boot modes

### Extended Filesystem Support
* **FAT32**: Default for maximum compatibility (with 4GB file size limit)
* **NTFS**: Support for larger files with integrated UEFI:NTFS bootloader
* **exFAT**: Combined large file support and cross-platform compatibility
* **F2FS** (experimental): Flash-friendly filesystem option

### Advanced Capabilities
* **Windows-To-Go**: Run Windows directly from USB without installation
* **Multi-Boot**: Install multiple Windows versions on a single USB
* **Persistent Storage**: Save settings and data across reboots
* **GPT Partitioning**: Support for drives larger than 2TB and flexible partition schemes

### User Interface
* Simple mode for basic operations
* Advanced mode for customized configurations
* Visual disk layout representation
* Detailed progress reporting
* Configuration profiles for repeated operations

## Installation

### Dependencies

#### Required Packages
```shell
sudo apt install git p7zip-full python3-pip python3-wxgtk4.0 grub2-common grub-pc-bin parted dosfstools ntfs-3g
```

#### Extended Filesystem Support
```shell
sudo apt install exfatprogs exfat-fuse
```

#### Advanced Partitioning
```shell
sudo apt install gdisk sgdisk gptfdisk
```

#### Windows-To-Go Support
```shell
sudo apt install wimlib-imagex chntpw
```

### Installation from Package Manager

#### Arch
```shell
yay -S woeusb-ds9
```

### Installation from Source Code
```shell
git clone https://github.com/WoeUSB/WoeUSB-DS9.git
cd WoeUSB-DS9
sudo pip3 install .
```

## Usage

### Command Line Interface

Basic usage:
```shell
woeusb --device source.iso /dev/sdX
```

Extended options:
```shell
woeusb --device source.iso /dev/sdX --filesystem exfat --windows-to-go --partition-scheme gpt
```

### Graphical Interface
```shell
woeusbgui
```

## Advanced Usage

### Windows-To-Go Creation
```shell
woeusb --windows-to-go win11.iso /dev/sdX
```

### Multi-Boot Configuration
```shell
woeusb --multi-boot --add-iso win10.iso --add-iso win11.iso /dev/sdX
```

### Custom Partition Layout
```shell
woeusb --device source.iso /dev/sdX --partition-scheme custom --partition "efi:fat32:500M" --partition "windows:ntfs:30G" --partition "data:exfat:remaining"
```

## Compatibility

### Supported Windows Versions
* Windows Vista, 7, 8.1, 10, 11
* All languages and editions (Home, Pro, Enterprise)
* Windows PE

### Supported Boot Modes
* Legacy BIOS boot
* UEFI boot
* Secure Boot (with limitations)

### Minimum Requirements
* USB drive: 8GB for basic installation, 32GB+ recommended for Windows-To-Go
* USB 3.0+ port recommended for best performance with Windows-To-Go

## Troubleshooting

See the [Troubleshooting Guide](doc/troubleshooting.md) for solutions to common issues.

## Development

Refer to the following documents for information about the project architecture and development roadmap:

* [Architecture Overview](ARCHITECTURE.md)
* [User Interface Assessment](UI_FLOW_ASSESSMENT.md)
* [Development Roadmap](ROADMAP.md)
* [Implementation Checklist](CHECKLIST.md)
* [Technical Design Specifications](TECHNICAL_DESIGN.md)

## License
WoeUSB-DS9 is distributed under the [GPL license](COPYING).