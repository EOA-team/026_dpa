""" """
from shutil import copytree, rmtree
import sys
import os 
from pathlib import Path
from pyprojroot import here
import yaml
import logging

BASE_PATH = here() / "code" / "tools" / "raw_to_hd"

logger = logging.getLogger(__name__)

def load_config(config_path: str | Path) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
        
def get_source_path(config: dict) -> Path:
    file_transfer_dict = config['file_transfer']
    _source_path = Path(file_transfer_dict['source_path'])
    return _source_path

def get_destination_path(config: dict) -> Path:
    file_transfer_dict = config['file_transfer']
    _destination_path = Path(file_transfer_dict['destination_path'])
    return _destination_path

def get_delete_after_transfer(config: dict) -> bool:
    file_transfer_dict = config['file_transfer']
    delete_after_transfer = file_transfer_dict['delete_after_transfer'] #should be bool type
    return delete_after_transfer

def get_config_path() -> Path:
    """Get config path - works for both script and executable."""
    if getattr(sys, 'frozen', False):
        # Running as executable (PyInstaller)
        base_path = Path(sys.executable).parent
    else:
        # Running as script - use pyprojroot only in dev
        base_path = BASE_PATH
    
    return base_path / "config.yaml"

def check_drive_mounted(path: str | Path) -> None:
    """Check if the drive or mount point for the given path is mounted.

    Raises:
        FileNotFoundError: If the drive/mount point is not mounted.
    """
    path = Path(path)
    mount_point = path.anchor  # e.g. '/' on Linux, 'D:\\' on Windows

    if not Path(mount_point).exists():
        raise FileNotFoundError(
            f"Drive or mount point not accessible: {mount_point}\n"
            "Check that the drive is mounted or network share is connected."
        )

    logger.info("Drive mounted: %s", mount_point)

def check_path_exists(path: str | Path) -> None:
    """Check if path exists.

    Raises:
        FileNotFoundError: If path does not exist.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    logger.info("Path exists: %s", path)


if __name__ == "__main__":

    config_path = get_config_path()
    config_dict = load_config(config_path)
    source_path = get_source_path(config_dict)
    destination_path = get_destination_path(config_dict)

    check_drive_mounted(path=destination_path)
    check_path_exists(path=source_path)

    print(f"Source path: {source_path}")
    print(f"Destination path: {destination_path}")

    copytree(source_path, destination_path, dirs_exist_ok=True)
    print(f"Copied {source_path} to {destination_path}")

    if get_delete_after_transfer(config_dict):
        print(f"Delete {source_path} ")
        rmtree(source_path)







   
