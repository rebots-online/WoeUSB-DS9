#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C)2025 Robin L. M. Cheung, MBA

"""
Filesystem handler modules for WoeUSB to support multiple filesystem types
including FAT32, NTFS, exFAT, F2FS, and BTRFS.

This module provides a common interface for different filesystem operations
and implementations for each supported filesystem type.
"""

import os
import subprocess
import shutil
from abc import ABC, abstractmethod
import WoeUSB.utils as utils
import WoeUSB.miscellaneous as miscellaneous

_ = miscellaneous.i18n

class FilesystemHandler(ABC):
    """Abstract base class defining interface for filesystem handlers"""
    
    @classmethod
    @abstractmethod
    def name(cls):
        """Return the name of the filesystem"""
        pass
        
    @classmethod
    @abstractmethod
    def supports_file_size_greater_than_4gb(cls):
        """
        Check if the filesystem supports files larger than 4GB
        
        Returns:
            bool: True if filesystem supports files > 4GB, False otherwise
        """
        pass
        
    @classmethod
    @abstractmethod
    def parted_fs_type(cls):
        """
        Return the filesystem type string to use with parted mkpart command
        
        Returns:
            str: Filesystem type string for parted
        """
        pass
        
    @classmethod
    @abstractmethod
    def format_partition(cls, partition, label):
        """
        Format the partition with this filesystem type
        
        Args:
            partition (str): Partition device path (e.g., /dev/sdX1)
            label (str): Filesystem label to apply
            
        Returns:
            int: 0 on success, non-zero on failure
        """
        pass
        
    @classmethod
    @abstractmethod
    def check_dependencies(cls):
        """
        Check if required dependencies for this filesystem are installed
        
        Returns:
            tuple: (is_available, missing_dependencies)
                is_available (bool): True if all dependencies are available
                missing_dependencies (list): List of missing dependency names
        """
        pass
        
    @classmethod
    def needs_uefi_support_partition(cls):
        """
        Check if this filesystem requires a separate UEFI support partition
        
        Returns:
            bool: True if UEFI support partition is needed, False otherwise
        """
        return False


class FatFilesystemHandler(FilesystemHandler):
    """Handler for FAT/FAT32 filesystem operations"""
    
    @classmethod
    def name(cls):
        return "FAT32"
        
    @classmethod
    def supports_file_size_greater_than_4gb(cls):
        return False
        
    @classmethod
    def parted_fs_type(cls):
        return "fat32"
        
    @classmethod
    def format_partition(cls, partition, label):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Creating FAT/FAT32 filesystem..."), "green")
        
        # Check for command_mkdosfs
        command_mkdosfs = utils.check_command("mkdosfs")
        if not command_mkdosfs:
            utils.print_with_color(_("Error: mkdosfs command not found"), "red")
            return 1
            
        # Format the first partition as FAT32 filesystem
        if subprocess.run([command_mkdosfs,
                        "-F", "32",
                        "-n", label,
                        "-v",
                        partition]).returncode != 0:
            utils.print_with_color(_("Error: Unable to create FAT32 filesystem"), "red")
            return 1
            
        return 0
        
    @classmethod
    def check_dependencies(cls):
        missing = []
        
        # Check for mkdosfs
        if not utils.check_command("mkdosfs"):
            missing.append("dosfstools")
            
        return (len(missing) == 0, missing)


class NtfsFilesystemHandler(FilesystemHandler):
    """Handler for NTFS filesystem operations"""
    
    @classmethod
    def name(cls):
        return "NTFS"
        
    @classmethod
    def supports_file_size_greater_than_4gb(cls):
        return True
        
    @classmethod
    def parted_fs_type(cls):
        return "ntfs"
        
    @classmethod
    def format_partition(cls, partition, label):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Creating NTFS filesystem..."), "green")
        
        # Check for mkntfs command
        command_mkntfs = utils.check_command("mkntfs")
        if not command_mkntfs:
            utils.print_with_color(_("Error: mkntfs command not found"), "red")
            return 1
            
        # Format the partition as NTFS
        if subprocess.run([command_mkntfs,
                        "-f",  # Fast format
                        "-L", label,
                        "-v",
                        partition]).returncode != 0:
            utils.print_with_color(_("Error: Unable to create NTFS filesystem"), "red")
            return 1
            
        return 0
        
    @classmethod
    def check_dependencies(cls):
        missing = []
        
        # Check for mkntfs
        if not utils.check_command("mkntfs"):
            missing.append("ntfs-3g")
            
        return (len(missing) == 0, missing)
        
    @classmethod
    def needs_uefi_support_partition(cls):
        """NTFS requires a separate UEFI support partition for UEFI booting"""
        return True


class ExfatFilesystemHandler(FilesystemHandler):
    """Handler for exFAT filesystem operations"""
    
    @classmethod
    def name(cls):
        return "exFAT"
        
    @classmethod
    def supports_file_size_greater_than_4gb(cls):
        return True
        
    @classmethod
    def parted_fs_type(cls):
        # parted doesn't directly support exfat
        # but it can be created after partition creation
        return "fat32"
        
    @classmethod
    def format_partition(cls, partition, label):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Creating exFAT filesystem..."), "green")
        
        # Check for mkexfatfs command
        command_mkexfat = utils.check_command("mkexfatfs") or utils.check_command("mkfs.exfat")
        if not command_mkexfat:
            utils.print_with_color(_("Error: mkexfatfs/mkfs.exfat command not found"), "red")
            return 1
            
        # Format the partition as exFAT
        cmd = [command_mkexfat, "-n", label, partition]
        if subprocess.run(cmd).returncode != 0:
            utils.print_with_color(_("Error: Unable to create exFAT filesystem"), "red")
            return 1
            
        return 0
        
    @classmethod
    def check_dependencies(cls):
        missing = []
        
        # Check for mkexfatfs or mkfs.exfat
        if not (utils.check_command("mkexfatfs") or utils.check_command("mkfs.exfat")):
            missing.append("exfatprogs or exfat-utils")
            
        return (len(missing) == 0, missing)


class F2fsFilesystemHandler(FilesystemHandler):
    """Handler for F2FS (Flash-Friendly File System) operations"""
    
    @classmethod
    def name(cls):
        return "F2FS"
        
    @classmethod
    def supports_file_size_greater_than_4gb(cls):
        return True
        
    @classmethod
    def parted_fs_type(cls):
        # parted doesn't directly support f2fs
        # but we can create the filesystem after partition creation
        return "ext4"
        
    @classmethod
    def format_partition(cls, partition, label):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Creating F2FS filesystem..."), "green")
        
        # Check for mkfs.f2fs command
        command_mkf2fs = utils.check_command("mkfs.f2fs")
        if not command_mkf2fs:
            utils.print_with_color(_("Error: mkfs.f2fs command not found"), "red")
            return 1
            
        # Format the partition as F2FS
        if subprocess.run([command_mkf2fs,
                        "-l", label,
                        "-f",  # Force overwrite
                        partition]).returncode != 0:
            utils.print_with_color(_("Error: Unable to create F2FS filesystem"), "red")
            return 1
            
        return 0
        
    @classmethod
    def check_dependencies(cls):
        missing = []
        
        # Check for mkfs.f2fs
        if not utils.check_command("mkfs.f2fs"):
            missing.append("f2fs-tools")
            
        return (len(missing) == 0, missing)
        
    @classmethod
    def needs_uefi_support_partition(cls):
        """F2FS requires a separate UEFI support partition for UEFI booting"""
        return True


class BtrfsFilesystemHandler(FilesystemHandler):
    """Handler for Btrfs filesystem operations"""
    
    @classmethod
    def name(cls):
        return "BTRFS"
        
    @classmethod
    def supports_file_size_greater_than_4gb(cls):
        return True
        
    @classmethod
    def parted_fs_type(cls):
        return "btrfs"
        
    @classmethod
    def format_partition(cls, partition, label):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Creating BTRFS filesystem..."), "green")
        
        # Check for mkfs.btrfs command
        command_mkbtrfs = utils.check_command("mkfs.btrfs")
        if not command_mkbtrfs:
            utils.print_with_color(_("Error: mkfs.btrfs command not found"), "red")
            return 1
            
        # Format the partition as BTRFS
        if subprocess.run([command_mkbtrfs,
                        "-L", label,
                        "-f",  # Force overwrite
                        partition]).returncode != 0:
            utils.print_with_color(_("Error: Unable to create BTRFS filesystem"), "red")
            return 1
            
        return 0
        
    @classmethod
    def check_dependencies(cls):
        missing = []
        
        # Check for mkfs.btrfs
        if not utils.check_command("mkfs.btrfs"):
            missing.append("btrfs-progs")
            
        return (len(missing) == 0, missing)
        
    @classmethod
    def needs_uefi_support_partition(cls):
        """BTRFS requires a separate UEFI support partition for UEFI booting"""
        return True


# Mapping of filesystem types to handler classes
_FILESYSTEM_HANDLERS = {
    "FAT": FatFilesystemHandler,
    "FAT32": FatFilesystemHandler,
    "NTFS": NtfsFilesystemHandler,
    "EXFAT": ExfatFilesystemHandler,
    "F2FS": F2fsFilesystemHandler,
    "BTRFS": BtrfsFilesystemHandler
}


def get_filesystem_handler(fs_type):
    """
    Factory function to get the appropriate filesystem handler
    
    Args:
        fs_type (str): Filesystem type name (case-insensitive)
        
    Returns:
        FilesystemHandler: The appropriate filesystem handler class
        
    Raises:
        ValueError: If the filesystem type is not supported
    """
    fs_type = fs_type.upper()
    if fs_type not in _FILESYSTEM_HANDLERS:
        raise ValueError(_("Unsupported filesystem type: {0}").format(fs_type))
        
    return _FILESYSTEM_HANDLERS[fs_type]


def get_available_filesystem_handlers():
    """
    Get a list of available filesystem handlers based on installed dependencies
    
    Returns:
        list: List of available filesystem type names
    """
    available = []
    for fs_type, handler in _FILESYSTEM_HANDLERS.items():
        is_available, _ = handler.check_dependencies()
        if is_available:
            available.append(fs_type)
            
    return available


def get_optimal_filesystem_for_iso(source_path):
    """
    Determine the optimal filesystem type for the given source ISO/directory
    based on file sizes and available filesystem handlers
    
    Args:
        source_path (str): Path to source ISO or directory
        
    Returns:
        str: Optimal filesystem type name
    """
    # Check if there are files larger than 4GB
    has_large_files = utils.check_fat32_filesize_limitation(source_path)
    
    # Get available filesystems
    available_fs = get_available_filesystem_handlers()
    
    # If no large files, prefer FAT32 for maximum compatibility
    if not has_large_files and "FAT" in available_fs:
        return "FAT"
        
    # If large files exist, prefer filesystems in this order
    preferred_fs = ["EXFAT", "NTFS", "F2FS", "BTRFS"]
    
    for fs in preferred_fs:
        if fs in available_fs:
            return fs
            
    # If we reach here and FAT is available, use it despite limitations
    if "FAT" in available_fs:
        return "FAT"
        
    # If nothing is available, default to FAT and let the error handling
    # in the main code deal with missing dependencies
    return "FAT"