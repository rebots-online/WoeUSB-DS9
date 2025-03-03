#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C)2025 Robin L. M. Cheung, MBA

"""
Virtual disk handler modules for WoeUSB to support ISO images larger than 4GB.

This module provides implementation for various virtual disk formats (VHD, QCOW2, IMG)
that can handle large Windows ISOs without the 4GB limitation of FAT32.
"""

import os
import subprocess
import shutil
import pathlib
import tempfile
import WoeUSB.utils as utils
import WoeUSB.miscellaneous as miscellaneous
from abc import ABC, abstractmethod

_ = miscellaneous.i18n

class VirtualDiskHandler(ABC):
    """Abstract base class defining interface for virtual disk handlers"""
    
    @classmethod
    @abstractmethod
    def name(cls):
        """Return the name of the virtual disk format"""
        pass
        
    @classmethod
    @abstractmethod
    def file_extension(cls):
        """Return the file extension for this virtual disk type"""
        pass
    
    @classmethod
    @abstractmethod
    def create_virtual_disk(cls, target_path, size_bytes, label=None):
        """
        Create a new virtual disk image file
        
        Args:
            target_path (str): Path where to create the virtual disk
            size_bytes (int): Size of the virtual disk in bytes
            label (str, optional): Label for the disk
            
        Returns:
            int: 0 on success, non-zero on failure
        """
        pass
    
    @classmethod
    @abstractmethod
    def mount_virtual_disk(cls, disk_path, mount_point):
        """
        Mount a virtual disk to a filesystem path
        
        Args:
            disk_path (str): Path to the virtual disk file
            mount_point (str): Path where to mount the virtual disk
            
        Returns:
            int: 0 on success, non-zero on failure
        """
        pass
    
    @classmethod
    @abstractmethod
    def unmount_virtual_disk(cls, disk_path, mount_point):
        """
        Unmount a previously mounted virtual disk
        
        Args:
            disk_path (str): Path to the virtual disk file
            mount_point (str): Path where the virtual disk is mounted
            
        Returns:
            int: 0 on success, non-zero on failure
        """
        pass
    
    @classmethod
    @abstractmethod
    def make_bootable(cls, disk_path, windows_source):
        """
        Make the virtual disk bootable with Windows
        
        Args:
            disk_path (str): Path to the virtual disk file
            windows_source (str): Path to Windows ISO or mounted media
            
        Returns:
            int: 0 on success, non-zero on failure
        """
        pass
    
    @classmethod
    @abstractmethod
    def check_dependencies(cls):
        """
        Check if required dependencies for this virtual disk format are available
        
        Returns:
            tuple: (is_available, missing_dependencies)
                is_available (bool): True if all dependencies are available
                missing_dependencies (list): List of missing dependency names
        """
        pass


class VhdVirtualDiskHandler(VirtualDiskHandler):
    """Handler for VHD virtual disk operations"""
    
    @classmethod
    def name(cls):
        return "VHD"
    
    @classmethod
    def file_extension(cls):
        return ".vhd"
    
    @classmethod
    def create_virtual_disk(cls, target_path, size_bytes, label=None):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Creating VHD virtual disk image..."), "green")
        
        # Check for qemu-img
        command_qemu_img = utils.check_command("qemu-img")
        if not command_qemu_img:
            utils.print_with_color(_("Error: qemu-img command not found"), "red")
            return 1
        
        # Calculate size in GB (rounded up)
        size_gb = (size_bytes + (1024**3) - 1) // (1024**3)
        
        # Create the VHD image (fixed size)
        if subprocess.run([command_qemu_img, 
                          "create", 
                          "-f", "vpc", 
                          target_path, 
                          f"{size_gb}G"]).returncode != 0:
            utils.print_with_color(_("Error: Unable to create VHD virtual disk"), "red")
            return 1
        
        return 0
    
    @classmethod
    def mount_virtual_disk(cls, disk_path, mount_point):
        utils.check_kill_signal()
        
        # Check for guestmount
        command_guestmount = utils.check_command("guestmount")
        if not command_guestmount:
            utils.print_with_color(_("Error: guestmount command not found"), "red")
            return 1
        
        # Ensure mount point exists
        os.makedirs(mount_point, exist_ok=True)
        
        # Mount the VHD using libguestfs
        if subprocess.run([command_guestmount, 
                          "-a", disk_path, 
                          "-m", "/dev/sda1", 
                          "--rw", 
                          mount_point]).returncode != 0:
            utils.print_with_color(_("Error: Unable to mount VHD virtual disk"), "red")
            return 1
        
        return 0
    
    @classmethod
    def unmount_virtual_disk(cls, disk_path, mount_point):
        utils.check_kill_signal()
        
        # Check if mounted
        if not os.path.ismount(mount_point):
            return 0
        
        # Unmount using fusermount
        command_fusermount = utils.check_command("fusermount")
        if not command_fusermount:
            utils.print_with_color(_("Error: fusermount command not found"), "red")
            return 1
        
        if subprocess.run([command_fusermount, 
                          "-u", 
                          mount_point]).returncode != 0:
            utils.print_with_color(_("Error: Unable to unmount VHD virtual disk"), "red")
            return 1
        
        return 0
    
    @classmethod
    def make_bootable(cls, disk_path, windows_source):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Making VHD bootable for Windows..."), "green")
        
        # This is a complex operation that requires:
        # 1. Mounting the VHD
        # 2. Creating partitions
        # 3. Copying Windows files
        # 4. Setting boot sectors
        
        # Create a temporary directory for mounting
        temp_mount = tempfile.mkdtemp(prefix="WoeUSB.vhd.")
        
        try:
            # Mount the VHD
            if cls.mount_virtual_disk(disk_path, temp_mount) != 0:
                return 1
            
            # Copy Windows files (simplified, would need more complex logic in practice)
            for root, dirs, files in os.walk(windows_source):
                rel_path = os.path.relpath(root, windows_source)
                target_dir = os.path.join(temp_mount, rel_path)
                os.makedirs(target_dir, exist_ok=True)
                
                for file in files:
                    shutil.copy2(
                        os.path.join(root, file),
                        os.path.join(target_dir, file)
                    )
            
            # Unmount the VHD
            cls.unmount_virtual_disk(disk_path, temp_mount)
            
            return 0
        except Exception as e:
            utils.print_with_color(_("Error: {0}").format(str(e)), "red")
            return 1
        finally:
            # Clean up
            if os.path.exists(temp_mount):
                cls.unmount_virtual_disk(disk_path, temp_mount)
                shutil.rmtree(temp_mount, ignore_errors=True)
    
    @classmethod
    def check_dependencies(cls):
        missing = []
        
        # Check for qemu-img
        if not utils.check_command("qemu-img"):
            missing.append("qemu-utils")
        
        # Check for guestmount (libguestfs)
        if not utils.check_command("guestmount"):
            missing.append("libguestfs-tools")
        
        # Check for fusermount
        if not utils.check_command("fusermount"):
            missing.append("fuse")
        
        return (len(missing) == 0, missing)


class Qcow2VirtualDiskHandler(VirtualDiskHandler):
    """Handler for QCOW2 virtual disk operations"""
    
    @classmethod
    def name(cls):
        return "QCOW2"
    
    @classmethod
    def file_extension(cls):
        return ".qcow2"
    
    @classmethod
    def create_virtual_disk(cls, target_path, size_bytes, label=None):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Creating QCOW2 virtual disk image..."), "green")
        
        # Check for qemu-img
        command_qemu_img = utils.check_command("qemu-img")
        if not command_qemu_img:
            utils.print_with_color(_("Error: qemu-img command not found"), "red")
            return 1
        
        # Calculate size in GB (rounded up)
        size_gb = (size_bytes + (1024**3) - 1) // (1024**3)
        
        # Create the QCOW2 image
        if subprocess.run([command_qemu_img, 
                          "create", 
                          "-f", "qcow2", 
                          target_path, 
                          f"{size_gb}G"]).returncode != 0:
            utils.print_with_color(_("Error: Unable to create QCOW2 virtual disk"), "red")
            return 1
        
        return 0
    
    @classmethod
    def mount_virtual_disk(cls, disk_path, mount_point):
        utils.check_kill_signal()
        
        # Check for guestmount
        command_guestmount = utils.check_command("guestmount")
        if not command_guestmount:
            utils.print_with_color(_("Error: guestmount command not found"), "red")
            return 1
        
        # Ensure mount point exists
        os.makedirs(mount_point, exist_ok=True)
        
        # Mount the QCOW2 using libguestfs
        if subprocess.run([command_guestmount, 
                          "-a", disk_path, 
                          "-m", "/dev/sda1", 
                          "--rw", 
                          mount_point]).returncode != 0:
            utils.print_with_color(_("Error: Unable to mount QCOW2 virtual disk"), "red")
            return 1
        
        return 0
    
    @classmethod
    def unmount_virtual_disk(cls, disk_path, mount_point):
        utils.check_kill_signal()
        
        # Same implementation as VHD
        # Check if mounted
        if not os.path.ismount(mount_point):
            return 0
        
        # Unmount using fusermount
        command_fusermount = utils.check_command("fusermount")
        if not command_fusermount:
            utils.print_with_color(_("Error: fusermount command not found"), "red")
            return 1
        
        if subprocess.run([command_fusermount, 
                          "-u", 
                          mount_point]).returncode != 0:
            utils.print_with_color(_("Error: Unable to unmount QCOW2 virtual disk"), "red")
            return 1
        
        return 0
    
    @classmethod
    def make_bootable(cls, disk_path, windows_source):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Making QCOW2 bootable for Windows..."), "green")
        
        # Implementation similar to VHD
        temp_mount = tempfile.mkdtemp(prefix="WoeUSB.qcow2.")
        
        try:
            # Mount the QCOW2
            if cls.mount_virtual_disk(disk_path, temp_mount) != 0:
                return 1
            
            # Copy Windows files
            for root, dirs, files in os.walk(windows_source):
                rel_path = os.path.relpath(root, windows_source)
                target_dir = os.path.join(temp_mount, rel_path)
                os.makedirs(target_dir, exist_ok=True)
                
                for file in files:
                    shutil.copy2(
                        os.path.join(root, file),
                        os.path.join(target_dir, file)
                    )
            
            # Unmount the QCOW2
            cls.unmount_virtual_disk(disk_path, temp_mount)
            
            return 0
        except Exception as e:
            utils.print_with_color(_("Error: {0}").format(str(e)), "red")
            return 1
        finally:
            # Clean up
            if os.path.exists(temp_mount):
                cls.unmount_virtual_disk(disk_path, temp_mount)
                shutil.rmtree(temp_mount, ignore_errors=True)
    
    @classmethod
    def check_dependencies(cls):
        missing = []
        
        # Check for qemu-img
        if not utils.check_command("qemu-img"):
            missing.append("qemu-utils")
        
        # Check for guestmount (libguestfs)
        if not utils.check_command("guestmount"):
            missing.append("libguestfs-tools")
        
        # Check for fusermount
        if not utils.check_command("fusermount"):
            missing.append("fuse")
        
        return (len(missing) == 0, missing)


class RawImgVirtualDiskHandler(VirtualDiskHandler):
    """Handler for raw IMG virtual disk operations"""
    
    @classmethod
    def name(cls):
        return "RAW"
    
    @classmethod
    def file_extension(cls):
        return ".img"
    
    @classmethod
    def create_virtual_disk(cls, target_path, size_bytes, label=None):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Creating RAW IMG virtual disk image..."), "green")
        
        # Check for dd
        command_dd = utils.check_command("dd")
        if not command_dd:
            utils.print_with_color(_("Error: dd command not found"), "red")
            return 1
        
        # Create the IMG file
        if subprocess.run([command_dd, 
                          "if=/dev/zero", 
                          f"of={target_path}", 
                          "bs=1M", 
                          f"count={size_bytes // (1024*1024)}"]).returncode != 0:
            utils.print_with_color(_("Error: Unable to create RAW IMG virtual disk"), "red")
            return 1
        
        # Create a partition table and filesystem on the img
        # Using losetup to create a loop device
        command_losetup = utils.check_command("losetup")
        if not command_losetup:
            utils.print_with_color(_("Error: losetup command not found"), "red")
            return 1
        
        # Find a free loop device
        result = subprocess.run([command_losetup, "-f"], stdout=subprocess.PIPE)
        loop_device = result.stdout.decode('utf-8').strip()
        
        # Associate the loop device with the img file
        if subprocess.run([command_losetup, loop_device, target_path]).returncode != 0:
            utils.print_with_color(_("Error: Unable to associate loop device"), "red")
            return 1
        
        try:
            # Create a partition table
            if subprocess.run(["parted", "-s", loop_device, "mklabel", "msdos"]).returncode != 0:
                utils.print_with_color(_("Error: Unable to create partition table"), "red")
                return 1
            
            # Create a partition covering the entire disk
            if subprocess.run(["parted", "-s", loop_device, "mkpart", "primary", "ntfs", "1MiB", "100%"]).returncode != 0:
                utils.print_with_color(_("Error: Unable to create partition"), "red")
                return 1
            
            # Make sure the kernel sees the new partition table
            subprocess.run(["partprobe", loop_device])
            
            # Format the partition
            partition_device = f"{loop_device}p1" if loop_device.endswith("p") else f"{loop_device}1"
            
            # Create NTFS filesystem on the partition
            if label:
                mkntfs_args = ["mkntfs", "-f", "-L", label, partition_device]
            else:
                mkntfs_args = ["mkntfs", "-f", partition_device]
                
            if subprocess.run(mkntfs_args).returncode != 0:
                utils.print_with_color(_("Error: Unable to create filesystem"), "red")
                return 1
            
            return 0
        finally:
            # Cleanup: detach the loop device
            subprocess.run([command_losetup, "-d", loop_device])
    
    @classmethod
    def mount_virtual_disk(cls, disk_path, mount_point):
        utils.check_kill_signal()
        
        # Check for losetup
        command_losetup = utils.check_command("losetup")
        if not command_losetup:
            utils.print_with_color(_("Error: losetup command not found"), "red")
            return 1
        
        # Find a free loop device
        result = subprocess.run([command_losetup, "-f"], stdout=subprocess.PIPE)
        loop_device = result.stdout.decode('utf-8').strip()
        
        # Associate the loop device with the img file
        if subprocess.run([command_losetup, loop_device, disk_path]).returncode != 0:
            utils.print_with_color(_("Error: Unable to associate loop device"), "red")
            return 1
        
        # Ensure mount point exists
        os.makedirs(mount_point, exist_ok=True)
        
        try:
            # Make sure the kernel sees the partitions
            subprocess.run(["partprobe", loop_device])
            
            # Determine the partition device
            partition_device = f"{loop_device}p1" if loop_device.endswith("p") else f"{loop_device}1"
            
            # Mount the partition
            if subprocess.run(["mount", partition_device, mount_point]).returncode != 0:
                utils.print_with_color(_("Error: Unable to mount image partition"), "red")
                subprocess.run([command_losetup, "-d", loop_device])
                return 1
            
            # Store the loop device somewhere for unmounting
            with open(f"{mount_point}/.loop_device", "w") as f:
                f.write(loop_device)
            
            return 0
        except Exception as e:
            utils.print_with_color(_("Error: {0}").format(str(e)), "red")
            subprocess.run([command_losetup, "-d", loop_device])
            return 1
    
    @classmethod
    def unmount_virtual_disk(cls, disk_path, mount_point):
        utils.check_kill_signal()
        
        # Check if mounted
        if not os.path.ismount(mount_point):
            return 0
        
        try:
            # Get the loop device from the stored file
            loop_device = None
            loop_device_file = f"{mount_point}/.loop_device"
            if os.path.exists(loop_device_file):
                with open(loop_device_file, "r") as f:
                    loop_device = f.read().strip()
            
            # Unmount
            if subprocess.run(["umount", mount_point]).returncode != 0:
                utils.print_with_color(_("Error: Unable to unmount image"), "red")
                return 1
            
            # Detach the loop device if we found it
            if loop_device:
                command_losetup = utils.check_command("losetup")
                if command_losetup:
                    subprocess.run([command_losetup, "-d", loop_device])
            
            return 0
        except Exception as e:
            utils.print_with_color(_("Error: {0}").format(str(e)), "red")
            return 1
    
    @classmethod
    def make_bootable(cls, disk_path, windows_source):
        utils.check_kill_signal()
        
        utils.print_with_color(_("Making RAW IMG bootable for Windows..."), "green")
        
        # Similar to the other implementations
        temp_mount = tempfile.mkdtemp(prefix="WoeUSB.img.")
        
        try:
            # Mount the IMG
            if cls.mount_virtual_disk(disk_path, temp_mount) != 0:
                return 1
            
            # Copy Windows files
            for root, dirs, files in os.walk(windows_source):
                rel_path = os.path.relpath(root, windows_source)
                target_dir = os.path.join(temp_mount, rel_path)
                os.makedirs(target_dir, exist_ok=True)
                
                for file in files:
                    shutil.copy2(
                        os.path.join(root, file),
                        os.path.join(target_dir, file)
                    )
            
            # Unmount the IMG
            cls.unmount_virtual_disk(disk_path, temp_mount)
            
            return 0
        except Exception as e:
            utils.print_with_color(_("Error: {0}").format(str(e)), "red")
            return 1
        finally:
            # Clean up
            if os.path.exists(temp_mount):
                cls.unmount_virtual_disk(disk_path, temp_mount)
                shutil.rmtree(temp_mount, ignore_errors=True)
    
    @classmethod
    def check_dependencies(cls):
        missing = []
        
        # Check for dd
        if not utils.check_command("dd"):
            missing.append("coreutils")
        
        # Check for losetup
        if not utils.check_command("losetup"):
            missing.append("util-linux")
        
        # Check for parted
        if not utils.check_command("parted"):
            missing.append("parted")
        
        # Check for partprobe
        if not utils.check_command("partprobe"):
            missing.append("parted")
        
        # Check for mkntfs
        if not utils.check_command("mkntfs"):
            missing.append("ntfs-3g")
        
        return (len(missing) == 0, missing)


# Mapping of virtual disk types to handler classes
_VIRTUALDISK_HANDLERS = {
    "VHD": VhdVirtualDiskHandler,
    "QCOW2": Qcow2VirtualDiskHandler,
    "RAW": RawImgVirtualDiskHandler
}


def get_virtualdisk_handler(vd_type):
    """
    Factory function to get the appropriate virtual disk handler
    
    Args:
        vd_type (str): Virtual disk type name (case-insensitive)
        
    Returns:
        VirtualDiskHandler: The appropriate virtual disk handler class
        
    Raises:
        ValueError: If the virtual disk type is not supported
    """
    vd_type = vd_type.upper()
    if vd_type not in _VIRTUALDISK_HANDLERS:
        raise ValueError(_("Unsupported virtual disk type: {0}").format(vd_type))
        
    return _VIRTUALDISK_HANDLERS[vd_type]


def get_available_virtualdisk_handlers():
    """
    Get a list of available virtual disk handlers based on installed dependencies
    
    Returns:
        list: List of available virtual disk type names
    """
    available = []
    for vd_type, handler in _VIRTUALDISK_HANDLERS.items():
        is_available, _ = handler.check_dependencies()
        if is_available:
            available.append(vd_type)
            
    return available


def get_optimal_virtualdisk_for_iso(source_path):
    """
    Determine the optimal virtual disk type for the given source ISO/directory
    
    Args:
        source_path (str): Path to source ISO or directory
        
    Returns:
        str: Optimal virtual disk type name
    """
    # Get available virtual disk formats
    available_vd = get_available_virtualdisk_handlers()
    
    # Prefer formats in this order
    preferred_vd = ["RAW", "VHD", "QCOW2"]
    
    for vd in preferred_vd:
        if vd in available_vd:
            return vd
            
    # If nothing is available, default to RAW
    return "RAW"