# WoeUSB-DS9 Architecture Documentation

## System Overview

WoeUSB-DS9 is a Linux utility for creating bootable Windows USB installers from Windows ISO images or DVDs. The software supports both legacy BIOS booting and UEFI booting, with filesystem options including FAT32 and NTFS.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          WoeUSB System                              │
├─────────────────┬─────────────────────────┬───────────────────────┬─┘
│                 │                         │                       │
│  Command Line   │         Core            │      Utilities        │
│  Interface      │     Processing          │                       │
│ (woeusb script) │     (core.py)           │     (utils.py)        │
│                 │                         │                       │
└─────────────────┘                         │                       │
                   │                        │                       │
                   │                        │                       │
┌─────────────────┐│                        │                       │
│                 ││                        │                       │
│  GUI Interface  ││                        │                       │
│ (woeusbgui,     ││                        │                       │
│  gui.py)        ││                        │                       │
│                 ││                        │                       │
└─────────────────┘│                        │                       │
                   │                        │                       │
┌──────────────────┴──────────┐  ┌──────────┴───────────┐  ┌───────┴───────────────┐
│                             │  │                      │  │                       │
│ Filesystem Operations       │  │ Device Operations    │  │ Workarounds           │
│ - Format partitions         │  │ - Partition creation │  │ - UEFI:NTFS support  │
│ - Mount/unmount             │  │ - Device detection   │  │ - Windows 7 UEFI boot │
│ - Copy files                │  │ - Block operations   │  │ - Boot flag fixes     │
│                             │  │                      │  │                       │
└─────────────────────────────┘  └──────────────────────┘  └───────────────────────┘
```

## Process Flow

```
┌────────────────┐     ┌───────────────────┐     ┌─────────────────────┐
│                │     │                   │     │                     │
│ Parse Command  │────▶│ Check Runtime     │────▶│ Prepare Target      │
│ Line Arguments │     │ Dependencies      │     │ Device/Partition    │
│                │     │                   │     │                     │
└────────────────┘     └───────────────────┘     └──────────┬──────────┘
                                                            │
                                                            ▼
┌────────────────┐     ┌───────────────────┐     ┌─────────────────────┐
│                │     │                   │     │                     │
│ Mount Source & │◀────│ Create & Format   │◀────│ Check Source Files  │
│ Target FS      │     │ Target Partition  │     │ & Select Filesystem │
│                │     │                   │     │                     │
└───────┬────────┘     └───────────────────┘     └─────────────────────┘
        │
        ▼
┌────────────────┐     ┌───────────────────┐     ┌─────────────────────┐
│                │     │                   │     │                     │
│ Copy Files     │────▶│ Install Boot      │────▶│ Apply Workarounds   │
│ from Source    │     │ Loaders           │     │ (as needed)         │
│                │     │                   │     │                     │
└────────────────┘     └───────────────────┘     └──────────┬──────────┘
                                                            │
                                                            ▼
                                                 ┌─────────────────────┐
                                                 │                     │
                                                 │ Unmount & Cleanup   │
                                                 │                     │
                                                 └─────────────────────┘
```

## Filesystem Selection Logic

```
┌────────────────┐
│                │
│ Start with     │
│ Target FS=FAT  │
│                │
└───────┬────────┘
        │
        ▼
┌────────────────────────┐    Yes    ┌─────────────────────────┐
│                        │           │                         │
│ Any file > 4GB in      ├──────────▶│ Switch Target FS to     │
│ source filesystem?     │           │ NTFS                    │
│                        │           │                         │
└───────┬────────────────┘           └────────────┬────────────┘
        │                                         │
        │ No                                      │
        ▼                                         ▼
┌────────────────┐                    ┌─────────────────────────┐
│                │                    │                         │
│ Continue with  │                    │ Create UEFI:NTFS        │
│ FAT filesystem │                    │ Support Partition       │
│                │                    │                         │
└────────────────┘                    └─────────────────────────┘
```

## UEFI:NTFS Support Implementation

```
┌────────────────────────┐
│                        │
│ Target filesystem      │
│ is set to NTFS         │
│                        │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│                        │
│ Create main NTFS       │
│ partition for Windows  │
│ files                  │
│                        │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│                        │
│ Create small FAT16     │
│ partition (marked as   │
│ FAT12 but Parted       │
│ doesn't support FAT12) │
│                        │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────────────────────────────┐
│                                                │
│ Download UEFI:NTFS bootloader                  │
│ (https://github.com/pbatard/rufus/raw/         │
│  master/res/uefi/uefi-ntfs.img)                │
│                                                │
└───────────┬────────────────────────────────────┘
            │
            ▼
┌────────────────────────┐
│                        │
│ Write UEFI:NTFS image  │
│ to second partition    │
│                        │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────┐
│                                                        │
│ The UEFI:NTFS bootloader serves as a bridge:           │
│ 1. UEFI firmware boots this small FAT partition        │
│ 2. UEFI:NTFS loader then enables UEFI to boot from     │
│    the NTFS partition                                  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Filesystem Types and Constraints

| Filesystem | Max File Size | Max Volume Size | UEFI Boot Support | Notes |
|------------|---------------|-----------------|-------------------|-------|
| FAT32      | 4GB           | 32GB (typical)  | Native           | Default choice, directly bootable in UEFI mode |
| NTFS       | 16TB          | 256TB           | Via UEFI:NTFS    | Requires UEFI:NTFS bridge or firmware NTFS support |
| exFAT      | 16EB          | 128PB           | Not Supported    | Not currently implemented |
| F2FS       | 4GB - 3.94TB  | 16TB            | Not Supported    | Not currently implemented |

## Current Limitations

1. **FAT32 4GB file size limit**: The system automatically switches to NTFS when files larger than 4GB are detected.
2. **UEFI booting from NTFS**: Requires downloading and installing the UEFI:NTFS bootloader.
3. **Filesystem options**: Currently limited to FAT32 and NTFS.