# Windows 11 To-Go Technical Specification

This document provides detailed technical specifications for implementing Windows 11 To-Go functionality in WoeUSB-DS9, allowing users to run Windows 11 directly from a USB drive without installation.

## 1. Overview

Windows 11 To-Go is not officially supported by Microsoft (unlike the previous Windows To-Go feature in Windows 10 Enterprise/Education), but can be implemented through careful system preparation and configuration. This implementation focuses on:

1. Bypassing TPM 2.0 and Secure Boot requirements
2. Creating an appropriate partition structure
3. Preparing Windows 11 for hardware portability
4. Optimizing performance on removable media

## 2. Requirements

### 2.1 Hardware Requirements

- **USB Drive**: Minimum 64GB, USB 3.0+ recommended
- **Speed**: Minimum 200MB/s read, 100MB/s write recommended
- **Quality**: Enterprise-grade flash recommended for longevity

### 2.2 Software Dependencies

- Windows 11 ISO (any edition)
- wimlib-imagex (for Linux-based image extraction)
- DISM (optional, for Windows-based image handling)
- reged/chntpw (for offline registry editing)
- NTFS-3g with full read/write support

## 3. Implementation Details

### 3.1 Partition Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ Partition 1: Microsoft Reserved (16MB)                          │
├─────────────────────────────────────────────────────────────────┤
│ Partition 2: EFI System Partition - FAT32 (200MB)               │
├─────────────────────────────────────────────────────────────────┤
│ Partition 3: Windows 11 OS - NTFS (40GB+)                       │
├─────────────────────────────────────────────────────────────────┤
│ Partition 4: Data/Recovery - NTFS/exFAT (Remaining)             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Partition Details

#### Microsoft Reserved Partition
- Size: 16MB
- Type: Microsoft Reserved Partition
- Format: No filesystem
- GUID: E3C9E316-0B5C-4DB8-817D-F92DF00215AE

#### EFI System Partition
- Size: 200MB
- Type: EFI System Partition
- Format: FAT32
- GUID: C12A7328-F81F-11D2-BA4B-00A0C93EC93B
- Content: Windows Boot Manager, GRUB2 for multi-boot

#### Windows 11 OS Partition
- Size: 40GB+ (minimum, more recommended)
- Type: Basic Data Partition
- Format: NTFS with 4K clusters
- GUID: EBD0A0A2-B9E5-4433-87C0-68B6B72699C7
- Content: Windows 11 OS files

#### Data/Recovery Partition (Optional)
- Size: Remaining space
- Type: Basic Data Partition
- Format: NTFS or exFAT (user choice)
- GUID: EBD0A0A2-B9E5-4433-87C0-68B6B72699C7
- Content: User data, recovery files

### 3.3 Implementation Steps

```python
def create_windows11_to_go(iso_path, target_device, data_partition_format="NTFS"):
    """Create Windows 11 To-Go on target device"""
    # 1. Create partition layout
    create_gpt_partition_table(target_device)
    create_msr_partition(target_device, "16M")
    efi_partition = create_esp_partition(target_device, "200M")
    win_partition = create_windows_partition(target_device, "40G")
    data_partition = create_data_partition(target_device, "remaining", data_partition_format)
    
    # 2. Format partitions
    format_esp_partition(efi_partition)
    format_windows_partition(win_partition)
    format_data_partition(data_partition, data_partition_format)
    
    # 3. Mount Windows ISO and extract Windows 11
    extract_windows11_wim(iso_path, win_partition)
    
    # 4. Configure Windows 11 for portability
    apply_tpm_bypass(win_partition)
    configure_portable_drivers(win_partition)
    optimize_for_removable_media(win_partition)
    
    # 5. Install boot files
    install_boot_files(iso_path, efi_partition)
    
    # 6. Final configurations
    configure_boot_entries(target_device, efi_partition)
```

### 3.4 TPM and Secure Boot Bypass

Registry modifications to bypass Windows 11 hardware checks:

```python
def apply_tpm_bypass(windows_partition):
    """Apply registry modifications to bypass TPM and Secure Boot requirements"""
    # Mount Windows registry
    registry_path = os.path.join(windows_partition, "Windows/System32/config/SYSTEM")
    
    # Use reged to modify offline registry
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as script:
        script.write('cd HKLM\\SYSTEM\\Setup\n')
        script.write('add LabConfig\n')
        script.write('cd LabConfig\n')
        script.write('add DWORD BypassTPMCheck 1\n')
        script.write('add DWORD BypassSecureBootCheck 1\n')
        script.write('add DWORD BypassRAMCheck 1\n')
        
        # Optional: Skip OOBE screens
        script.write('cd HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\OOBE\n')
        script.write('add DWORD BypassNRO 1\n')
        
        script.write('quit\n')
    
    # Apply changes
    subprocess.run(["reged", "-C", registry_path, script.name])
```

### 3.5 Hardware Portability Configuration

Optimize Windows for different hardware:

```python
def configure_portable_drivers(windows_partition):
    """Configure Windows for hardware portability"""
    # Disable driver signature enforcement
    bcdedit_path = os.path.join(windows_partition, "Windows/System32/bcdedit.exe")
    subprocess.run([bcdedit_path, "/store", f"{windows_partition}/Boot/BCD", 
                   "/set", "{default}", "nointegritychecks", "yes"])
    
    # Enable all hardware profiles
    registry_path = os.path.join(windows_partition, "Windows/System32/config/SYSTEM")
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as script:
        script.write('cd HKLM\\SYSTEM\\CurrentControlSet\\Control\\CriticalDeviceDatabase\n')
        script.write('add DWORD AllDevices 1\n')
        script.write('quit\n')
    
    subprocess.run(["reged", "-C", registry_path, script.name])
```

### 3.6 Performance Optimization

Configure Windows for optimal performance on removable media:

```python
def optimize_for_removable_media(windows_partition):
    """Optimize Windows configuration for running from removable media"""
    # Disable hibernation
    disable_hibernation(windows_partition)
    
    # Disable paging file
    disable_paging_file(windows_partition)
    
    # Configure write caching
    enable_write_caching(windows_partition)
    
    # Disable unnecessary services
    disable_unnecessary_services(windows_partition)
    
    # Configure power settings
    configure_power_settings(windows_partition)
```

## 4. User Interface Integration

### 4.1 Windows 11 To-Go Creation Wizard

A dedicated wizard for Windows 11 To-Go creation will guide users through:

1. **ISO Selection**: Choose Windows 11 ISO
2. **Device Selection**: Select target USB device
3. **Partition Configuration**:
   - OS partition size (min 40GB)
   - Data partition format (NTFS/exFAT)
4. **Advanced Options**:
   - Language and regional settings
   - Driver inclusion options
   - Performance optimization level
5. **Creation Process**:
   - Partitioning and formatting
   - File extraction
   - System configuration
   - Boot setup

### 4.2 Progress Reporting

Detailed progress reporting during Windows 11 To-Go creation:

```python
class Windows11ToGoProgress:
    def __init__(self, ui_callback):
        self.ui_callback = ui_callback
        self.stages = [
            {"name": "Preparing device", "weight": 10},
            {"name": "Creating partitions", "weight": 10},
            {"name": "Extracting Windows files", "weight": 60},
            {"name": "Configuring system", "weight": 15},
            {"name": "Setting up boot", "weight": 5}
        ]
        self.current_stage = 0
        self.stage_progress = 0
    
    def update_stage(self, stage_index, stage_progress=0):
        """Update progress to a specific stage with optional sub-progress"""
        self.current_stage = stage_index
        self.stage_progress = stage_progress
        self._report_progress()
    
    def increment_stage_progress(self, increment):
        """Increment progress within the current stage"""
        self.stage_progress += increment
        self._report_progress()
    
    def _report_progress(self):
        """Calculate and report overall progress"""
        # Calculate weighted total progress
        total_weight = sum(stage["weight"] for stage in self.stages)
        completed_weight = sum(self.stages[i]["weight"] for i in range(self.current_stage))
        current_weight = self.stages[self.current_stage]["weight"] * (self.stage_progress / 100)
        
        total_progress = (completed_weight + current_weight) / total_weight * 100
        
        # Report progress
        self.ui_callback(
            stage_name=self.stages[self.current_stage]["name"],
            stage_progress=self.stage_progress,
            total_progress=total_progress
        )
```

## 5. Testing Strategy

### 5.1 Compatibility Testing

- Test on different USB drive models and capacities
- Verify boot on various PC manufacturers and models
- Test with different UEFI implementations
- Verify Secure Boot compatibility (with bypass)

### 5.2 Performance Testing

- Boot time measurements
- Application launch time comparisons
- Disk I/O benchmarks on different USB 3.x controllers
- System responsiveness evaluation

### 5.3 Stability Testing

- Multiple boot cycle tests
- Hardware change simulations (different PCs)
- Sleep/wake cycles
- Windows Update testing

## 6. Known Limitations

1. **Performance Constraints**:
   - Overall performance will be lower than installed Windows
   - USB bus speed limitations affect responsiveness

2. **Hardware Support**:
   - May not work on all hardware combinations
   - Graphics driver issues on widely varying hardware

3. **Updates**:
   - Windows updates may occasionally break the TPM bypass
   - Feature updates may require re-preparation

4. **Microsoft Policy**:
   - Not officially supported by Microsoft
   - May be blocked in future Windows versions