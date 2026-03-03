"""Module for transferring data from drone to hard drive after a flight.

Scrapes trajectory data from the APX-20 sensor and transfers recording data
from the drone to the hard drive. Only supports one flight folder at a time
to ensure correct trajectory matching.
"""
import logging
from pathlib import Path
from shutil import copytree, rmtree
from code.file_utils import check_drive_mounted, copy_with_logging
from code.tools.postflightdtt.postflightdtt_helpers import get_flight_folder, get_resolved_config
from code.scrapers.trajectory_scraper import TrajectoryScraper

logger = logging.getLogger(__name__)

def drone_to_hd_transfer(config: dict) -> None:
    """Load config, scrape trajectory data, 
    and transfer recordings data from drone to hard drive."""
    logger.info("Starting Drone to Hard Drive Transfer")
    # Abort if Hard Drive not mounted
    check_drive_mounted(
        path=Path(config['file_transfer']['drone_to_hd']['destination_path']))
    # Get Flight Folder
    flight_folder = get_flight_folder(
        recordings_path=Path(config['file_transfer']['drone_to_hd']['source_path']).parent)
    # Load Resolve Config
    resolved_config = get_resolved_config(
        config=config,
        flight_folder=flight_folder)
    # Processing Steps
    scrape_trajectory_data(config=resolved_config)
    transfer_recordings_data(config=resolved_config)


def scrape_trajectory_data(config) -> None:
    """Scrape trajectory data from APX-20 and save to recordings data folder."""
    logger.info("Starting trajectory data scraping...")
    scraper = TrajectoryScraper(config=config['trajectory_scraper'])
    scraper.run()
    logger.info("Trajectory data scraping complete")


def transfer_recordings_data(config) -> None:
    """ Transfer recordings data from drone to hard drive, with cleanup after transfer. 
    Backup before transfer is possible if enabled in config."""
    # Transfer Recordings Data
    source_path = config['file_transfer']['drone_to_hd']['source_path']
    destination_path = config['file_transfer']['drone_to_hd']['destination_path']
    # Backup before transfer if enabled in config
    backup = config['file_transfer']['drone_to_hd']['backup']
    if backup:
        logger.info("Backup enabled - backing up source before transfer")
        backup_path = config['file_transfer']['drone_to_hd']['backup_path']
        copytree(src=source_path.parent,
                 dst=backup_path,
                 dirs_exist_ok=True,  # Allow overwriting existing data
                 copy_function=copy_with_logging
                 )
        logger.info("Backed up %s to %s", source_path.parent, backup_path)
    # Transfer data
    logger.info("Transferring recordings data...")
    copytree(src=source_path,
             dst=destination_path,
             dirs_exist_ok=True,  # Allow overwriting existing data
             copy_function=copy_with_logging
             )
    logger.info("Copied %s to %s", source_path, destination_path)
    # Cleanup
    rmtree(source_path)
    logger.info("Deleted all files in %s", source_path)
