""" """
from shutil import copytree
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
    source_path = Path(file_transfer_dict['source_path'])
    check_path_accessible(source_path)
    return source_path

def get_destination_path(config: dict) -> Path:
    file_transfer_dict = config['file_transfer']
    destination_path = Path(file_transfer_dict['destination_path'])
    check_path_accessible(destination_path)
    return destination_path

def get_delete_after_transfer(config: dict) -> bool:
    file_transfer_dict = config['file_transfer']
    delete_after_transfer = 
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

def check_path_accessible(path: str | Path) -> None:
    """Check if path is mounted and accessible.
    
    Raises:
        FileNotFoundError: If path does not exist or is not mounted.
        PermissionError: If path exists but is not writable.
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(
            f"Path not accessible: {path}\n"
            "Check that the drive is mounted or network share is connected."
        )
    if not os.access(path, os.W_OK):
        raise PermissionError(f"Path is not writable: {path}")
    
    logger.info("Path accessible: %s", path)


if __name__ == "__main__":
    config_path = get_config_path()
    config_dict = load_config(config_path)
    source_path = get_source_path(config_dict)
    destination_path = get_destination_path(config_dict)
    print(f"Source path: {source_path}")
    print(f"Destination path: {destination_path}")  

    copytree(source_path, destination_path, dirs_exist_ok=True)
    print(f"Copied {source_path} to {destination_path}")
   
