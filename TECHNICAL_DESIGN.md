# WoeUSB-DS9 Technical Design Document

This document provides detailed technical specifications for implementing extended filesystem support, multi-boot capability, and Windows-To-Go functionality in WoeUSB-DS9.

## 1. Filesystem Implementation Details

### 1.1 Filesystem Handler Architecture

```
┌─────────────────────────────────────────────┐
│              FilesystemHandler               │
├─────────────────────────────────────────────┤
│ + detect_source_filesystem()                │
│ + check_filesystem_compatibility()          │
│ + format_filesystem()                       │
│ + check_bootability()                       │
│ + setup_boot_support()                      │
└───────────────┬─────────────────────────────┘
                │
                ├─────────────────┬─────────────────┬─────────────────┐
                │                 │                 │                 │
┌───────────────▼───────┐ ┌───────▼───────────┐ ┌───▼───────────┐ ┌───▼───────────┐
│   FAT32Handler        │ │   NTFSHandler     │ │ exFATHandler  │ │ F2FSHandler   │
├─────────────────────┬─┤ ├───────────────────┤ ├───────────────┤ ├───────────────┤
│ + format()          │ │ + format()          │ │ + format()    │ │ + format()    │
│ + check_limits()    │ │ + check_limits()    │ │ + check_limits│ │ + check_limits│
│ + setup_boot()      │ │ + setup_boot()      │ │ + setup_boot()│ │ + setup_boot()│
└─────────────────────┘ │ + setup_uefi_ntfs() │ └───────────────┘ └───────────────┘
                        └───────────────────────┘
```

### 1.2 Filesystem Selection Algorithm

```
START
  |
  v
[Check ISO file sizes]
  |
  v
<Any file > 4GB?> ──Yes──> [NTFS or exFAT required]
  |                          |
  No                         v
  |                      <Available space > 32GB?> ──Yes──> [Recommend exFAT]
  v                          |                                 |
[Recommend FAT32]           No                                 v
  |                          |                         <Advanced mode enabled?> ──Yes──> [Show all options]
  |                          v                                 |                          |
  └─────────────────> [Recommend NTFS] <──────────────────────No                         v
                           |                                                     [User selects filesystem]
                           v                                                              |
                    <Windows 11 ISO?> ──Yes──> [Check Windows-To-Go option]               |
                           |                         |                                    |
                           No                        v                                    |
                           |              <WTG option selected?> ──Yes──> [Configure WTG partitions]
                           |                         |                          |
                           |                        No                          v
                           └─────────────────┬──────┘                  [Apply selected options]
                                            |                                   |
                                            v                                   v
                                   [Configure standard partitions] <───────────┘
                                            |
                                            v
                                          END
```

### 1.3 exFAT Implementation Specifics

exFAT will be implemented as a new filesystem option with the following characteristics:

1. **Dependencies**:
   - exfatprogs/exfat-utils for formatting
   - exfat-fuse for mounting on the host system

2. **Format Parameters**:
   ```
   mkexfatfs -n "Windows USB" [options] /dev/sdX1
   ```
   
   Parameters to optimize for USB media:
   - Cluster size: 128KB for large drives (>32GB)
   - Cluster size: 32KB for smaller drives

3. **Boot Support**:
   - Requires bootloader stage that supports exFAT
   - EFI System Partition (ESP) may be needed in some configurations
   - Compatibility layer for legacy BIOS boot

### 1.4 NTFS Enhancements

Improved NTFS support with integrated UEFI:NTFS bootloader:

1. **UEFI:NTFS Integration**:
   - Bundle UEFI:NTFS bootloader in `WoeUSB/data/uefi-ntfs.img`
   - Use bundled image instead of downloading from GitHub
   - Add fallback to download if bundle is corrupted

2. **NTFS Format Optimizations**:
   ```
   mkntfs --quick --cluster-size=4096 --no-indexing -L "Windows USB" /dev/sdX1
   ```

3. **NTFS Boot Configuration**:
   - Create second small FAT16 partition with UEFI:NTFS bootloader
   - Configure partition type codes correctly for firmware recognition
   - Add boot flag for legacy BIOS compatibility

## 2. Partition Management System

### 2.1 GPT Partition Table Implementation

```python
def create_gpt_partition_table(target_device):
    """Create GPT partition table on target device"""
    # Wipe existing partition table
    subprocess.run(["wipefs", "--all", target_device])
    
    # Create GPT partition table
    subprocess.run(["parted", "--script", target_device, "mklabel", "gpt"])
    
    # Create protective MBR for compatibility
    subprocess.run(["sgdisk", "--hybrid", target_device])
```

### 2.2 Partition Layout Templates

#### Standard Windows USB Layout (GPT)
```
┌─────────────────────────────────────────────────────────────────┐
│ Partition 1: Microsoft reserved (16MB)                          │
├─────────────────────────────────────────────────────────────────┤
│ Partition 2: EFI System Partition - FAT32 (200MB)               │
├─────────────────────────────────────────────────────────────────┤
│ Partition 3: Main Windows partition - NTFS/exFAT (Remaining)    │
└─────────────────────────────────────────────────────────────────┘
```

#### Windows-To-Go Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ Partition 1: Microsoft reserved (16MB)                          │
├─────────────────────────────────────────────────────────────────┤
│ Partition 2: EFI System Partition - FAT32 (200MB)               │
├─────────────────────────────────────────────────────────────────┤
│ Partition 3: Windows OS - NTFS (30GB+)                          │
├─────────────────────────────────────────────────────────────────┤
│ Partition 4: Windows data - NTFS/exFAT (Remaining)              │
└─────────────────────────────────────────────────────────────────┘
```

#### Multi-Boot Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ Partition 1: Microsoft reserved (16MB)                          │
├─────────────────────────────────────────────────────────────────┤
│ Partition 2: EFI System Partition - FAT32 (200MB)               │
├─────────────────────────────────────────────────────────────────┤
│ Partition 3: Shared data - exFAT (User-defined)                 │
├─────────────────────────────────────────────────────────────────┤
│ Partition 4: Windows 1 - NTFS/exFAT (User-defined)              │
├─────────────────────────────────────────────────────────────────┤
│ Partition 5+: Additional OSes - Various FS (User-defined)       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Partition Type Codes

| Partition Type | GPT GUID | MBR Code | Description |
|----------------|----------|----------|-------------|
| Microsoft Reserved | E3C9E316-0B5C-4DB8-817D-F92DF00215AE | 0x0C | Required for Windows |
| EFI System | C12A7328-F81F-11D2-BA4B-00A0C93EC93B | 0xEF | EFI bootloader partition |
| Windows Basic Data | EBD0A0A2-B9E5-4433-87C0-68B6B72699C7 | 0x07 | Windows NTFS partition |
| exFAT | 516E7CB4-6ECF-11D6-8FF8-00022D09712B | 0x07 | exFAT partition |
| Windows Recovery | DE94BBA4-06D1-4D40-A16A-BFD50179D6AC | 0x27 | Windows recovery partition |

## 3. Multi-Boot Implementation

### 3.1 Boot Manager Configuration

GRUB2 will be used as the primary boot manager with the following configuration:

```
menuentry "Windows 10" {
    insmod part_gpt
    insmod search_fs_uuid
    insmod chain
    search --fs-uuid --set=root XXXX-XXXX
    chainloader /EFI/Microsoft/Boot/bootmgfw.efi
}

menuentry "Windows 11 To-Go" {
    insmod part_gpt
    insmod search_fs_uuid
    insmod ntfs
    insmod chain
    search --fs-uuid --set=root YYYY-YYYY
    chainloader /EFI/Boot/bootx64.efi
}
```

### 3.2 Boot Manager Installation

```python
def install_grub_bootloader(target_device, efi_partition, config_entries):
    """Install GRUB bootloader for multi-boot support"""
    # Mount EFI partition
    subprocess.run(["mount", efi_partition, "/mnt/efi"])
    
    # Install GRUB for UEFI
    subprocess.run(["grub-install", "--target=x86_64-efi", 
                   "--efi-directory=/mnt/efi", "--boot-directory=/mnt/efi/boot",
                   "--removable", target_device])
    
    # Generate configuration
    generate_grub_config("/mnt/efi/boot/grub/grub.cfg", config_entries)
    
    # Unmount
    subprocess.run(["umount", "/mnt/efi"])
```

## 4. Windows-To-Go Implementation

### 4.1 Windows-To-Go Preparation

The Windows-To-Go functionality will require:

1. **Modified Partition Layout**:
   - GPT partition table
   - EFI System Partition (200MB)
   - Windows OS partition (min 30GB)
   - Optional data partition

2. **Windows Image Preparation**:
   ```python
   def prepare_windows_to_go_image(iso_path, target_partition):
       """Prepare Windows image for portable use"""
       # Mount ISO
       subprocess.run(["mount", "-o", "loop", iso_path, "/mnt/iso"])
       
       # Extract Windows image
       subprocess.run(["wimlib-imagex", "extract", "/mnt/iso/sources/install.wim", 
                      "1", target_partition, "--no-acls"])
       
       # Apply Windows-To-Go specific registry settings
       apply_wtg_registry_settings(target_partition)
       
       # Install bootloader
       install_windows_bootloader(target_partition)
       
       # Unmount
       subprocess.run(["umount", "/mnt/iso"])
   ```

3. **Registry Modifications**:
   - Disable hibernation
   - Configure for removable hardware
   - Set up hardware detection at boot
   - Enable TPM bypass for Windows 11

### 4.2 TPM Emulation for Windows 11

```python
def configure_tpm_bypass(windows_partition):
    """Configure registry bypass for TPM and Secure Boot requirements"""
    # Mount Windows registry
    registry_path = os.path.join(windows_partition, "Windows/System32/config/SYSTEM")
    
    # Use reged to modify offline registry hive
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as script:
        script.write('cd HKLM\\SYSTEM\\Setup\n')
        script.write('add LabConfig\n')
        script.write('cd LabConfig\n')
        script.write('add DWORD BypassTPMCheck 1\n')
        script.write('add DWORD BypassSecureBootCheck 1\n')
        script.write('add DWORD BypassRAMCheck 1\n')
        script.write('quit\n')
    
    # Apply changes
    subprocess.run(["reged", "-C", registry_path, script.name])
```

## 5. UI Enhancements for New Features

### 5.1 Filesystem and Partition Editor Component

```python
class DiskVisualizationPanel(wx.Panel):
    """Interactive disk visualization and partitioning panel"""
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        # Set up visualization
        self.disk_bitmap = wx.StaticBitmap(self)
        self.partition_sliders = []
        
        # Set up controls
        self.filesystem_choices = wx.Choice(self, choices=["FAT32", "NTFS", "exFAT", "F2FS"])
        self.partition_type_choices = wx.Choice(self, choices=["Primary", "EFI System", "MSR", "Data"])
        
        # Bind events
        self.filesystem_choices.Bind(wx.EVT_CHOICE, self.on_filesystem_changed)
        
        # Layout components
        self._do_layout()
    
    def update_visualization(self, partition_info):
        """Update the visual representation based on partition info"""
        # Generate disk image here
        # ...
        
    def on_filesystem_changed(self, event):
        """Handle filesystem selection changes"""
        selected_fs = self.filesystem_choices.GetStringSelection()
        # Update UI elements based on filesystem selection
        # ...
```

### 5.2 Configuration Profile System

```python
class ConfigProfile:
    """Configuration profile for saving/loading WoeUSB settings"""
    
    def __init__(self, name="Default"):
        self.name = name
        self.settings = {
            "filesystem": "FAT32",
            "partition_scheme": "MBR",
            "boot_options": {
                "windows_to_go": False,
                "multi_boot": False,
                "persistence": False
            },
            "partitions": []
        }
    
    def save(self, filename):
        """Save profile to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    @classmethod
    def load(cls, filename):
        """Load profile from JSON file"""
        profile = cls()
        with open(filename, 'r') as f:
            profile.settings = json.load(f)
        return profile
```

## 6. Integration Tests

### 6.1 Filesystem Format and Boot Tests

```python
def test_filesystem_format_and_boot(filesystem_type, device, iso_path):
    """Test formatting and booting with specified filesystem"""
    # Format device
    format_device(device, filesystem_type)
    
    # Install Windows
    install_windows(device, iso_path)
    
    # Test bootability (simulate in VM)
    result = test_boot_in_vm(device)
    
    return result
```

### 6.2 Multi-Boot Configuration Tests

```python
def test_multi_boot_configuration(device, iso_paths):
    """Test multi-boot setup with multiple Windows ISOs"""
    # Set up partitions
    setup_multi_boot_partitions(device, len(iso_paths))
    
    # Install each ISO
    for i, iso_path in enumerate(iso_paths):
        install_windows_to_partition(device, i+1, iso_path)
    
    # Install boot manager
    install_boot_manager(device)
    
    # Test bootability of each entry
    results = []
    for i in range(len(iso_paths)):
        results.append(test_boot_entry_in_vm(device, i))
    
    return results
```

## 7. Dependency Management

| Feature | Required Packages | Optional Packages |
|---------|-------------------|-------------------|
| exFAT support | exfatprogs/exfat-utils, exfat-fuse | - |
| NTFS support | ntfs-3g | ntfsprogs |
| GPT partitioning | gdisk, sgdisk | gptfdisk |
| Windows-To-Go | wimlib-imagex | dism (Windows) |
| TPM emulation | reged (chntpw) | - |
| Multi-boot | grub2 | os-prober |
| Boot management | efibootmgr | - |

The implementation will check for these dependencies and provide clear error messages if they are missing.