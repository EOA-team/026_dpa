import logging
from pathlib import Path
from shutil import copytree, rmtree
from code.file_utils import check_path_exists, check_drive_mounted,copy_with_logging, get_base_path
from code.yamlconfig_helper import  replace_config_placeholder, resolve_relative_paths
from code.scrapers.trajectory_scraper import TrajectoryScraper

logger = logging.getLogger(__name__)

def drone_to_hd_transfer(config: dict) -> None:
    logger.info("Starting Drone to Hard Drive Transfer")
    #Abort if Hard Drive not mounted
    check_drive_mounted(
        path=Path(config['file_transfer']['drone_to_hd']['destination_path']))
    #Get Flight Folder
    flight_folder = get_flight_folder(
        recordings_path= Path(config['file_transfer']['drone_to_hd']['source_path']).parent)
    #Load Resolve Config
    resolved_config =get_resolved_config(
        config=config, 
        flight_folder=flight_folder)
    #Processing Steps
    scrape_trajectory_data(config=resolved_config)
    transfer_recordings_data(config=resolved_config)

def get_flight_folder(recordings_path: Path) -> Path:
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
    check_path_exists(recordings_path, message="Check that the path is correct and HySpexAir recorded correctly.")
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

def get_resolved_config(config: dict, flight_folder: str) -> dict:
    """Replace placeholders and resolve relative paths in config."""
    replaced_config = replace_config_placeholder(
        config=config, 
        placeholder="{flight_folder}", 
        replacement=flight_folder
    )
    resolved_config = resolve_relative_paths(
        config=replaced_config, 
        base_path=get_base_path(__file__)
    )
    return resolved_config

# Scrape APX Trajectory Data
def scrape_trajectory_data(config) -> None:
    print(config['trajectory_scraper'])
    logger.info("Starting trajectory data scraping...")
    scraper = TrajectoryScraper(config=config['trajectory_scraper'])
    scraper.run_test()
    # TODO : Replace with correct run method 
    logger.info("Trajectory data scraping complete")

def transfer_recordings_data(config) -> None:
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
    #Transfer data
    logger.info("Transferring recordings data...")
    copytree(src=source_path, 
             dst=destination_path, 
             dirs_exist_ok=True, # Allow overwriting existing data
             copy_function=copy_with_logging
            )
    logger.info("Copied %s to %s", source_path, destination_path)
    #Cleanup
    rmtree(source_path)
    logger.info("Deleted all files in %s", source_path)






