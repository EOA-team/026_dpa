""" Basic helper functions for PostFlightDTT tool, 
which are being used in both drone_to_hd and hd_to_nas transfer modules."""
import logging
from shutil import copytree, rmtree
from code.file_utils import copy_with_logging
from code.file_utils import check_path_exists,  get_base_path
from code.yamlconfig_helper import replace_config_placeholder, resolve_relative_paths
from pathlib import Path

logger = logging.getLogger(__name__)

def get_flight_folder(recordings_path: Path) -> str:
    """Get the single recorded flight folder in recordings path after a flight.

    In case of multiple folders the pilot needs to be reminded to always run
    PostFlightDTT immediately after a flight, before starting a new one.

    Raises
    ------
    FileNotFoundError
        If no flight folder is found — possibly a HySpexAir recording issue.
    ValueError
        If more than one flight folder is found — PostFlightDTT was not run
        after the previous flight.
    """
    check_path_exists(
        recordings_path, message="Check that the path is correct and HySpexAir recorded correctly.")
    flight_folders = [f for f in recordings_path.iterdir() if f.is_dir()]

    if len(flight_folders) == 0:
        raise FileNotFoundError(
            f"No flight folder found in: {recordings_path}\n"
            "Check that HySpexAir recorded correctly and the path is correct."
        )
    if len(flight_folders) > 1:
        raise ValueError(
            f"Expected exactly one flight folder in: {recordings_path}\n"
            f"Found {len(flight_folders)}: {[f.name for f in flight_folders]}\n"
            "You might have started a new flight without running PostFlightDTT.exe\n"
            "You need to manually handle the data transfer in this case!"
        )

    return flight_folders[0].name


def get_resolved_config(config: dict, flight_folder: str | None = None) -> dict:
    """Replace placeholders with flight folder if available and resolve relative paths in config."""
    if flight_folder is not None:
        config = replace_config_placeholder(
            config=config,
            placeholder="{flight_folder}",
            replacement=flight_folder
        )
    resolved_config = resolve_relative_paths(
        config=config,
        base_path=get_base_path(__file__)
    )
    return resolved_config

def backup_source(src_path, dst_path) -> None:
    """Backup source before transfer if enabled in config."""
    logger.info("Backup enabled - backing up source before transfer")
    copytree(src=src_path,
                 dst=dst_path,
                 dirs_exist_ok=True,  # Allow overwriting existing data
                 copy_function=copy_with_logging
                 )
    logger.info("Backed up %s to %s", src_path, dst_path)

def transfer_data(src_path, dst_path) -> None:
    """ Transfer data from source to destination, with logging."""
    copytree(src=src_path,
            dst=dst_path,
            dirs_exist_ok=True,  # Allow overwriting existing data
            copy_function=copy_with_logging
            )
    logger.info("Copied %s to %s", src_path, dst_path)

def cleanup_source(src_path)-> None:
    """Delete all files in source path"""
    rmtree(src_path)
    logger.info("Deleted all files in %s", src_path)
