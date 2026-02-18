""" """
from shutil import copytree, rmtree, copy2
import sys
import os 
from pathlib import Path
from pyprojroot import here
import yaml
import logging
import subprocess
from code.scrapers.trajectory_scraper import TrajectoryScraper


BASE_PATH = here() / "code" / "tools" / "raw_to_hd"

logger = logging.getLogger(__name__)

def load_config(config_path: str | Path) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
        
def get_source_path(config: dict, filetransfer: str) -> Path:
    file_transfer_dict = config['file_transfer'][filetransfer]
    _source_path = Path(file_transfer_dict['source_path'])
    return _source_path

def get_destination_path(config: dict, filetransfer: str) -> Path:
    file_transfer_dict = config['file_transfer'][filetransfer]
    _destination_path = Path(file_transfer_dict['destination_path'])
    return _destination_path

def get_delete_after_transfer(config: dict, filetransfer: str) -> bool:
    file_transfer_dict = config['file_transfer'][filetransfer]
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


def check_path_exists(path: str | Path) -> None:
    """Check if path exists.

    Raises:
        FileNotFoundError: If path does not exist.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

def clear_folder(folder_path: Path | str) -> None:
    """Remove all contents and recreate the empty folder."""
    folder_path = Path(folder_path)
    rmtree(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)

def copy_with_logging(src, dst):
    """Copy function with size info."""
    size = Path(src).stat().st_size / (1024 * 1024)  # MB
    logger.info("Copying %s (%.2f MB)", Path(src).name, size)
    return copy2(src, dst)

if __name__ == "__main__":


    # Logger Settings
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Load Config
    config_path = get_config_path()
    config_dict = load_config(config_path)

    # Load Filetransfer Settings
    source_path_trajectory = get_source_path(config=config_dict, filetransfer="trajectory")
    destination_path_trajectory = get_destination_path(config=config_dict, filetransfer="trajectory")
    delete_trajectory_after_transfer = get_delete_after_transfer(config=config_dict, filetransfer="trajectory")

    source_path_recordings = get_source_path(config=config_dict, filetransfer="recordings")
    destination_path_recordings = get_destination_path(config=config_dict, filetransfer="recordings")
    delete_recordings_after_transfer = get_delete_after_transfer(config=config_dict, filetransfer="recordings")

    # Scrape APX Trajectory Data
    logger.info("Starting trajectory data scraping...")
    scraper = TrajectoryScraper(config_path=config_path)
    scraper.scrape()
    logger.info("Trajectory data scraping complete")

    # Transfer Trajectory Data
    logger.info("Transferring trajectory data...")
    check_drive_mounted(path=destination_path_trajectory)
    check_path_exists(path=source_path_trajectory)
    copytree(source_path_trajectory, destination_path_trajectory, dirs_exist_ok=True, copy_function=copy_with_logging)
    logger.info("Copied %s to %s", source_path_trajectory, destination_path_trajectory)

    if delete_trajectory_after_transfer:
        clear_folder(source_path_trajectory)
        logger.info("Deleted all files in %s", source_path_trajectory)

    # Transfer Recordings Data
    logger.info("Transferring recordings data...")
    check_drive_mounted(path=destination_path_recordings)
    check_path_exists(path=source_path_recordings)
    copytree(source_path_recordings, destination_path_recordings, dirs_exist_ok=True, copy_function=copy_with_logging)
    logger.info("Copied %s to %s", source_path_recordings, destination_path_recordings)

    if delete_recordings_after_transfer:
        clear_folder(source_path_recordings)
        logger.info("Deleted all files in %s", source_path_recordings)


    logger.info("All transfers complete")
    logger.warning("Please unmount Drive before disconnecting!")











   
