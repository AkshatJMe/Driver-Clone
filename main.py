import os
import time
import shutil
import string
import platform
import psutil
import json
from datetime import datetime
from pathlib import Path
import logging

# ------------------------------
# Setup
# ------------------------------
BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "usb_autocopy.log"
DEVICE_TRACKER = BASE_DIR / "copied_devices.json"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("USB AutoCopy started.")

DEST_FOLDER = Path.home() / "USB_Backup"
DEST_FOLDER.mkdir(parents=True, exist_ok=True)

# ------------------------------
# Reset Device Tracker on Startup
# ------------------------------
if DEVICE_TRACKER.exists():
    DEVICE_TRACKER.unlink()
    logging.info("Previous copied_devices.json deleted for fresh session.")

copied_devices = {}

# ------------------------------
# Save Tracker State
# ------------------------------
def save_tracker():
    with open(DEVICE_TRACKER, "w") as f:
        json.dump(copied_devices, f, indent=2)

# ------------------------------
# Get Mounted Drives
# ------------------------------
def get_mounted_drives():
    system = platform.system()
    drives = []
    if system == "Windows":
        for letter in string.ascii_uppercase:
            path = f"{letter}:/"
            if os.path.exists(path):
                drives.append(path)
    else:
        for part in psutil.disk_partitions(all=False):
            if 'media' in part.mountpoint or 'Volumes' in part.mountpoint:
                drives.append(part.mountpoint)
    return drives

# ------------------------------
# Generate a Unique ID for USB
# ------------------------------
def get_drive_id(path):
    try:
        usage = shutil.disk_usage(path)
        volume_name = Path(path).name or path[0]  # fallback to drive letter
        return f"{volume_name}_{usage.total}"
    except Exception as e:
        logging.warning(f"Failed to get drive ID for {path}: {e}")
        return None

# ------------------------------
# Copy From USB
# ------------------------------
def copy_from_usb(usb_path, drive_id):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    drive_letter = usb_path[0].upper()
    folder_name = f"{drive_letter}_{timestamp}"
    dest_subfolder = DEST_FOLDER / folder_name

    try:
        logging.info(f"Copying the files from {usb_path} to {dest_subfolder}")
        shutil.copytree(usb_path, dest_subfolder, dirs_exist_ok=True)
        copied_devices[drive_id] = timestamp
        save_tracker()
        logging.info(f"Copied from {usb_path} to {dest_subfolder}")
    except Exception as e:
        logging.error(f"Error copying from {usb_path}: {e}")

# ------------------------------
# Main Loop
# ------------------------------
def main():
    logging.info("Monitoring USB devices...")
    previous_drives = set(get_mounted_drives())

    while True:
        time.sleep(5)
        current_drives = set(get_mounted_drives())
        new_drives = current_drives - previous_drives

        for drive in new_drives:
            drive_id = get_drive_id(drive)
            if drive_id:
                if drive_id not in copied_devices:
                    logging.info(f"New USB detected: {drive} (ID: {drive_id})")
                    copy_from_usb(drive, drive_id)
                else:
                    logging.info(f"USB {drive} already copied this session. Skipping.")
        previous_drives = current_drives

if __name__ == "__main__":
    main()
